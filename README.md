# Resume-Ranking-API
The Resume Ranking API automates the process of ranking resumes based on job descriptions. It supports PDF and DOCX file formats for both job descriptions and resumes. The API extracts key ranking criteria from job descriptions and evaluates resumes using OpenAI’s GPT-4 model, ranking candidates on a scale of 0 to 5 across several criteria, including skills, experience, and certifications. Once the evaluation is complete, it generates an Excel file with the results, including a total score for each candidate. Users can customize the evaluation by providing job-specific ranking criteria in JSON format. Built using the FastAPI framework, the API ensures fast and efficient performance, with detailed logging for tracking activity. Robust error handling is in place to manage issues with file types, text extraction, and API errors, making the process seamless and reliable.

## Video Demo
Watch the demo video [here]
https://www.loom.com/share/e14c2c933ef146d6977e9cc609ecd102?sid=28de0091-7e08-4e73-abe1-c0ad7222cb87
