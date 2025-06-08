import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from openai import AzureOpenAI
import json


# ─── Initializtion ──────────────────────────────────────────────────

load_dotenv()
key = os.getenv("DocumentIntelligenceKEY")
endpoint = os.getenv("DocumentIntelligenceEndpoint")

OpenAiAzure_Key = os.getenv("OpenAiAzureKey")
OpenAiAzure_apiversion=os.getenv("api_version")
OpenAiAzure_endpoint=os.getenv("OpenAiAzureEndPoint")

HebrewTranslation=[
{
  "שם משפחה": "",
  "שם פרטי": "",
  "מספר זהות": "",
  "מין": "",
  "תאריך לידה": {
    "יום": "",
    "חודש": "",
    "שנה": ""
  },
  "כתובת": {
    "רחוב": "",
    "מספר בית": "",
    "כניסה": "",
    "דירה": "",
    "ישוב": "",
    "מיקוד": "",
    "תא דואר": ""
  },
  "טלפון קווי": "",
  "טלפון נייד": "",
  "סוג העבודה": "",
  "תאריך הפגיעה": {
    "יום": "",
    "חודש": "",
    "שנה": ""
  },
  "שעת הפגיעה": "",
  "מקום התאונה": "",
  "כתובת מקום התאונה": "",
  "תיאור התאונה": "",
  "האיבר שנפגע": "",
  "חתימה": "",
  "תאריך מילוי הטופס": {
    "יום": "",
    "חודש": "",
    "שנה": ""
  },
  "תאריך קבלת הטופס בקופה": {
    "יום": "",
    "חודש": "",
    "שנה": ""
  },
  "למילוי ע\"י המוסד הרפואי": {
    "חבר בקופת חולים": "",
    "מהות התאונה": "",
    "אבחנות רפואיות": ""
  }
}
]

EnglishTemplate=[
{
  "lastName": "",
  "firstName": "",
  "idNumber": "",
  "gender": "",
  "dateOfBirth": {
    "day": "",
    "month": "",
    "year": ""
  },
  "address": {
    "street": "",
    "houseNumber": "",
    "entrance": "",
    "apartment": "",
    "city": "",
    "postalCode": "",
    "poBox": ""
  },
  "landlinePhone": "",
  "mobilePhone": "",
  "jobType": "",
  "dateOfInjury": {
    "day": "",
    "month": "",
    "year": ""
  },
  "timeOfInjury": "",
  "accidentLocation": "",
  "accidentAddress": "",
  "accidentDescription": "",
  "injuredBodyPart": "",
  "signature": "",
  "formFillingDate": {
    "day": "",
    "month": "",
    "year": ""
  },
  "formReceiptDateAtClinic": {
    "day": "",
    "month": "",
    "year": ""
  },
  "medicalInstitutionFields": {
    "healthFundMember": "",
    "natureOfAccident": "",
    "medicalDiagnoses": ""
  }
}
]




# ─── Document Intelligence implemtion ──────────────────────────────────────────────────

document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

def readPDFfile(PathToPDF):
    """
    Analyze the layout of a PDF file using Azure Document Intelligence.

    Parameters
    ----------
    PathToPDF : str
        Path to the file document to be analyzed.

    Returns
    -------
    result : AnalyzeResult
        The analysis result.
    """
    
    
    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-layout", 
        PathToPDF , 
    )
    result =  poller.result() 
    return result
  
  
  
# ─── Azure OpenAi implemtion ──────────────────────────────────────────────────

def JsonGen(docInt_output , model_n):
    """
    Send request to Azure OpenAI and return the parsed Document Intelligence JSON result .

    Parameters
    ----------
    model_n : str
        The name of the Azure OpenAI deployment to use.
    docInt_output : AnalyzeResult
        The Document Intelligence analysis result to send to the model.

    Returns
    -------
    dict
        The model’s response parsed as a JSON object.
    """
    
    
    OpenAiAzure_deployment = model_n
    
    client = AzureOpenAI(
        api_version=OpenAiAzure_apiversion,
        azure_endpoint=OpenAiAzure_endpoint,
        api_key=OpenAiAzure_Key
    )
    
    response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": f""""You are an expert in generate Json from Document Intelligence output.
            You will recive an output when fileds content are in hebrew and you will follow the next steps:
            1. Extrect all fileds in the Document Intelligence output
            2. Comapre the Hebrew json and the English json to preform one-to-one in position translate
            3. You will generate and fill the fields exacly as in this data schema: {json.dumps(EnglishTemplate,indent=2)}
            
            The Hebrew Json: {json.dumps(HebrewTranslation,indent=2)}
            The English Json: {json.dumps(EnglishTemplate,indent=2)}
            
            Before return the json make sure all fileds are accuretly translated.
            """,
        },
        {
            "role": "user",
            "content": f"""This is an output from Document Intelligence:
            
            {docInt_output} 
            
            Generate the json as mentioned above""",
        }
    ],
    max_tokens=4096,
    temperature=0,
    top_p=1.0,
    model=OpenAiAzure_deployment,
    response_format={"type":"json_object"}
)

    Jsonresult = response.choices[0].message.content
    return Jsonresult





# ─── Accuracy and Completeness method implemtion ──────────────────────────────────────────────────

def listFromDict (DictToTransform):
  """
    Create a dict containing key–value pairs and return it along with its length.

    Parameters
    ----------
    DictToTransform : dict
        The dictionary to be transformed.

    Returns
    -------
      - resList : dict
          The final dictionary.
      - length : int
          Number of entries in the dictionary.
   """
   
  resList = {key : DictToTransform[key] for key in DictToTransform.keys()}
  return resList , len(resList)
  

def DatesTest(parsedjson):
    """
    Combine day, month, and year fields into a full date string and validate component lengths.

    Parameters
    ----------
    parsedjson : dict
        Expected to contain the keys "day", "month", and "year" with string values.

    Returns
    -------
    tuple
        - full_date : str
            The combined date in DDMMYYYY format.
        - errors : list
            List of error messages, empty if all components passed validation.
    """
    
    errors = []
    full_date = parsedjson["day"]+parsedjson["month"]+parsedjson["year"]
    try:
        len(parsedjson["day"]) == 2 and len(parsedjson["month"]) == 2 and len(parsedjson["year"]) == 4
    except (ValueError, TypeError):
        errors.append("Invalid data")
    return full_date , errors 



def AccuracyCompleteness(LLM4o_json , LLM4oMini_json , contentList):
    """
    Compute accuracy and completeness metrics comparing two LLM outputs.

    Parameters
    ----------
    LLM4o_json : str
        JSON string of the primary LLM’s result.
    LLM4oMini_json : str
        JSON string of the secondary LLM’s result.
    contentList : list
        A list of all content exsists in the Document Intelligence analysis result
        to validate LLM value content.

    Returns
    -------
    Accuracy : float
        Weighted accuracy percentage across all attributes.
    Completeness : float
        Percentage of non-empty attributes in the LLM result.
    errors : list
        Any date‐format validation errors encountered.
    """
    
    
    #Initaliztion
    parsedLLM4o_json = json.loads(LLM4o_json)
    parsedLLM4oMini_json = json.loads(LLM4oMini_json)
    
    LLM4o_List = {}
    LLM4oMini = {}
    errors=[]
    
    dates_to_check = ["dateOfBirth" , "dateOfInjury" , "formFillingDate" , "formReceiptDateAtClinic"]
    
    spicel_attributes = [dateobj for dateobj in dates_to_check]
    spicel_attributes.append("address")
    spicel_attributes.append("medicalInstitutionFields")
    
    JsonLen = len(dates_to_check) * 3
    
    
    # Store each LLM result’s attributes in normalized dict
    
    for key in parsedLLM4o_json.keys():
      if key in spicel_attributes:
        continue
      else:
        LLM4o_List[key] = parsedLLM4o_json[key]
        LLM4oMini[key] = parsedLLM4oMini_json[key]
        JsonLen +=1
    
    
    for key in dates_to_check:
      resLLM4o = DatesTest(parsedLLM4o_json[key])
      resLLM4oMini = DatesTest(parsedLLM4oMini_json[key])
      LLM4o_List[key+"_Date"] =  resLLM4o[0]
      LLM4oMini[key+"_Date"] =  resLLM4oMini[0]
      errors.append(resLLM4o[1])

         
    for key in spicel_attributes:
      if key not in dates_to_check:
        resLLM4o = listFromDict(parsedLLM4o_json[key])
        resLLM4oMini = listFromDict(parsedLLM4oMini_json[key])
        
        for att in resLLM4o[0].keys():
          LLM4o_List[key+"_"+att] =  resLLM4o[0][att]
        
        for att in resLLM4oMini[0].keys():
          LLM4oMini[key+"_"+att] =  resLLM4oMini[0][att]
          
        JsonLen += resLLM4o[1]
    
    
    #Accuracy calculation

    # 1
    common_keys = LLM4o_List.keys() & LLM4oMini.keys()

    common_pairs = { k: LLM4o_List[k] for k in common_keys if LLM4o_List[k] == LLM4oMini[k] }
    print(f"len(common_pairs) {len(common_pairs)}")
    
    common_pairs_acuracy = len(common_pairs) / JsonLen
    
    
    # 2
    accuracy_values_count = 0

    for value in LLM4o_List.values():
      if len(value) > 0 :
        words = value.split()
        print(words)
        if len([x for x in words if x in contentList]) == len(words):
          accuracy_values_count += 1 
      else:
          accuracy_values_count += 1 
        
    LLM4o_List_accuracy = accuracy_values_count / JsonLen
    
    
    Accuracy = (LLM4o_List_accuracy *  0.75  + common_pairs_acuracy * 0.25)  * 100
    
    
    #Completness calculation
    
    empty_call = sum(1 for v in LLM4o_List.values() if v == "")
    Completness = ((JsonLen-empty_call) / JsonLen) *100

    return Accuracy,  Completness, errors
    
    

  
    