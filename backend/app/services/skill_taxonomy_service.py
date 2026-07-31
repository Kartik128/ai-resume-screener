import re
from typing import Dict, List, Set, Tuple


class SkillTaxonomyService:
    """Comprehensive Cross-Industry (Tech & Non-Tech) Skill Taxonomy & NLP N-Gram Keyword Extraction Engine.
    Covers Healthcare, Legal, Finance, Marketing, HR, Construction, Supply Chain, Retail, Customer Support,
    Software Engineering, Data Science, AI, Product Management, Education, Real Estate, Media, and more.
    """

    SKILL_TAXONOMY: Dict[str, Tuple[str, List[str]]] = {
        # --- TECH: Programming Languages ---
        "python": ("Programming Language", ["py", "python3", "python2"]),
        "java": ("Programming Language", ["core java", "javaee", "j2ee", "java se", "java 8", "java 11", "java 17"]),
        "javascript": ("Programming Language", ["js", "es6", "es2015", "ecmascript", "vanilla js"]),
        "typescript": ("Programming Language", ["ts", "typescript 4", "typescript 5"]),
        "c++": ("Programming Language", ["cpp", "cplusplus", "c plus plus"]),
        "c#": ("Programming Language", ["csharp", "c sharp", "dotnet", ".net"]),
        "golang": ("Programming Language", ["go", "go lang", "go programming"]),
        "rust": ("Programming Language", ["rustlang", "rust programming"]),
        "ruby": ("Programming Language", ["ruby on rails", "rails", "ror"]),
        "php": ("Programming Language", ["laravel", "symfony", "wordpress", "php 8"]),
        "swift": ("Programming Language", ["ios development", "swiftui", "xcode"]),
        "kotlin": ("Programming Language", ["android development", "android sdk"]),
        "sql": ("Database & Query", ["t-sql", "pl/sql", "ansi sql", "sql server", "plsql"]),
        "r": ("Data Analysis Language", ["r programming", "rstudio", "r language"]),
        "scala": ("Programming Language", ["apache spark scala", "akka"]),
        "perl": ("Programming Language", ["perl scripting"]),
        "matlab": ("Scientific Computing", ["matlab programming", "simulink"]),
        "bash": ("Scripting", ["shell scripting", "bash scripting", "unix shell", "powershell"]),
        "vba": ("Scripting", ["excel vba", "macros", "visual basic for applications"]),
        "dart": ("Programming Language", ["flutter", "flutter development"]),
        "elixir": ("Programming Language", ["phoenix framework"]),
        "haskell": ("Programming Language", ["functional programming"]),
        "assembly": ("Programming Language", ["assembly language", "asm"]),
        "cobol": ("Programming Language", ["mainframe cobol"]),
        "fortran": ("Scientific Computing", ["fortran programming"]),

        # --- TECH: Web & Frontend Frameworks ---
        "react": ("Web Framework", ["reactjs", "react.js", "react native", "react hooks", "react context"]),
        "next.js": ("Web Framework", ["nextjs", "next js", "next", "server side rendering", "ssr"]),
        "vue.js": ("Web Framework", ["vue", "vuejs", "vue 3", "nuxt"]),
        "angular": ("Web Framework", ["angularjs", "angular 2", "angular 12", "angular 14", "angular 15"]),
        "svelte": ("Web Framework", ["sveltekit"]),
        "html5": ("Frontend", ["html", "semantic html", "html markup"]),
        "css3": ("Frontend", ["css", "sass", "scss", "less", "postcss"]),
        "tailwind css": ("Frontend", ["tailwind", "tailwindcss"]),
        "bootstrap": ("Frontend", ["responsive design", "bootstrap 5"]),
        "jquery": ("Frontend", ["jquery ui"]),
        "webpack": ("Build Tools", ["vite", "parcel", "rollup", "esbuild", "bundler"]),
        "storybook": ("UI Development", ["component library", "design system"]),
        "three.js": ("3D/WebGL", ["webgl", "webxr"]),

        # --- TECH: Backend Frameworks ---
        "fastapi": ("Backend Framework", ["fast api"]),
        "django": ("Backend Framework", ["django rest framework", "drf", "django orm"]),
        "flask": ("Backend Framework", ["flask api", "flask rest"]),
        "node.js": ("Backend Framework", ["nodejs", "node", "express"]),
        "express.js": ("Backend Framework", ["expressjs", "express framework"]),
        "spring boot": ("Backend Framework", ["spring", "spring mvc", "spring cloud", "spring security"]),
        "asp.net": ("Backend Framework", [".net core", "dotnet core", "asp.net core", "web api"]),
        "nestjs": ("Backend Framework", ["nest js", "nest framework"]),
        "rails": ("Backend Framework", ["ruby on rails", "ror"]),
        "laravel": ("Backend Framework", ["php laravel"]),
        "fastify": ("Backend Framework", ["fastify framework"]),

        # --- TECH: API & Architecture ---
        "rest api": ("Architecture", ["restful apis", "rest web services", "restful api", "http apis"]),
        "graphql": ("Architecture", ["apollo graphql", "graphql api", "graphql schema"]),
        "grpc": ("Architecture", ["protocol buffers", "protobuf"]),
        "websockets": ("Architecture", ["websocket", "real-time communication", "socket.io"]),
        "microservices": ("Architecture", ["microservice architecture", "distributed systems", "service mesh"]),
        "event-driven architecture": ("Architecture", ["event-driven", "event sourcing", "cqrs"]),
        "api design": ("Architecture", ["openapi", "swagger", "api documentation"]),

        # --- TECH: Databases ---
        "postgresql": ("Database", ["postgres", "pgsql", "pg"]),
        "mysql": ("Database", ["mariadb", "mysql server"]),
        "mongodb": ("Database", ["mongo", "nosql", "mongodb atlas"]),
        "redis": ("Database", ["in-memory cache", "redis cache", "caching"]),
        "elasticsearch": ("Database", ["elastic search", "elk stack", "opensearch"]),
        "cassandra": ("Database", ["apache cassandra", "cql"]),
        "dynamodb": ("Database", ["amazon dynamodb", "aws dynamodb"]),
        "oracle": ("Database", ["oracle db", "oracle database", "plsql"]),
        "mssql": ("Database", ["sql server", "microsoft sql server", "t-sql"]),
        "sqlite": ("Database", ["sqlite3"]),
        "neo4j": ("Database", ["graph database", "graph db", "cypher"]),
        "cockroachdb": ("Database", ["cockroach db"]),
        "firebase": ("Database", ["firebase firestore", "firebase realtime"]),
        "supabase": ("Database", ["supabase db"]),

        # --- TECH: Data Warehouse & Analytics ---
        "snowflake": ("Data Warehouse", ["snowflake db", "snowflake cloud"]),
        "google bigquery": ("Data Warehouse", ["bigquery", "bq"]),
        "apache hive": ("Data Warehouse", ["hive", "hql"]),
        "redshift": ("Data Warehouse", ["amazon redshift", "aws redshift"]),
        "databricks": ("Data Platform", ["databricks workspace", "delta lake", "unity catalog"]),
        "apache spark": ("Big Data", ["pyspark", "spark streaming", "spark sql"]),
        "hadoop": ("Big Data", ["hdfs", "mapreduce", "hbase", "oozie"]),
        "kafka": ("Message Queue", ["apache kafka", "kafka streams", "confluent"]),
        "rabbitmq": ("Message Queue", ["amqp", "message broker"]),
        "airflow": ("Data Engineering", ["apache airflow", "workflow orchestration", "dag"]),
        "dbt": ("Data Transformation", ["data build tool", "dbt cloud", "dbt core"]),
        "fivetran": ("Data Integration", ["etl", "elt", "data pipeline", "data ingestion"]),

        # --- TECH: Machine Learning & AI ---
        "machine learning": ("Artificial Intelligence", ["ml", "predictive modeling", "ml engineering"]),
        "deep learning": ("Artificial Intelligence", ["dl", "neural networks", "deep neural"]),
        "artificial intelligence": ("Artificial Intelligence", ["ai", "generative ai", "genai", "gen ai"]),
        "pytorch": ("Deep Learning Framework", ["torch", "torchvision"]),
        "tensorflow": ("Deep Learning Framework", ["tf", "keras", "tensorflow 2"]),
        "scikit-learn": ("ML Library", ["sklearn", "scikit learn"]),
        "xgboost": ("ML Library", ["xgb", "gradient boosting", "lightgbm", "catboost"]),
        "nlp": ("Artificial Intelligence", ["natural language processing", "text mining", "llm", "bert", "gpt", "transformer"]),
        "computer vision": ("Artificial Intelligence", ["cv", "image recognition", "object detection", "yolo", "opencv"]),
        "reinforcement learning": ("Artificial Intelligence", ["rl", "policy gradient"]),
        "langchain": ("LLM Framework", ["llama index", "semantic kernel", "rag", "retrieval augmented"]),
        "hugging face": ("AI Platform", ["huggingface", "transformers library"]),
        "mlflow": ("MLOps", ["mlops", "model registry", "experiment tracking"]),
        "feature engineering": ("Data Science", ["feature selection", "data preprocessing"]),
        "a/b testing": ("Analytics", ["ab testing", "hypothesis testing", "statistical testing"]),
        "statistics": ("Data Science", ["statistical analysis", "regression", "probability"]),

        # --- TECH: Data Analysis & BI ---
        "pandas": ("Data Analysis", ["dataframe", "pandas library"]),
        "numpy": ("Data Analysis", ["scipy", "numerical computing"]),
        "matplotlib": ("Data Visualization", ["seaborn", "plotly", "visualization library"]),
        "power bi": ("Data Analytics & BI", ["powerbi", "microsoft bi", "dax", "power query", "power platform"]),
        "tableau": ("Data Analytics & BI", ["tableau server", "tableau desktop", "tableau cloud"]),
        "looker": ("Data Analytics & BI", ["looker studio", "google looker", "lookml"]),
        "qlik": ("Data Analytics & BI", ["qlikview", "qlik sense"]),
        "excel": ("Data Analytics", ["advanced excel", "vlookup", "pivot tables", "excel formulas", "spreadsheets"]),
        "google analytics": ("Digital Analytics", ["ga4", "google analytics 4", "web analytics"]),

        # --- TECH: Cloud Platforms ---
        "aws": ("Cloud Platform", ["amazon web services", "ec2", "s3", "lambda", "rds", "ecs", "eks", "cloudformation"]),
        "microsoft azure": ("Cloud Platform", ["azure", "azure devops", "azure ad", "azure functions"]),
        "google cloud platform": ("Cloud Platform", ["gcp", "google cloud", "gke", "cloud run", "cloud storage"]),
        "alibaba cloud": ("Cloud Platform", ["aliyun"]),

        # --- TECH: DevOps, CI/CD & Infrastructure ---
        "docker": ("DevOps & Containers", ["containerization", "docker compose", "dockerfile"]),
        "kubernetes": ("DevOps & Containers", ["k8s", "container orchestration", "helm", "kustomize"]),
        "terraform": ("Infrastructure as Code", ["iac", "hashicorp terraform", "infrastructure automation"]),
        "ansible": ("Configuration Management", ["ansible playbook", "chef", "puppet"]),
        "ci/cd": ("DevOps", ["continuous integration", "continuous deployment", "pipeline", "continuous delivery"]),
        "jenkins": ("CI/CD", ["jenkins pipeline", "jenkins ci"]),
        "github actions": ("CI/CD", ["gha", "workflow automation"]),
        "gitlab ci": ("CI/CD", ["gitlab pipeline"]),
        "circleci": ("CI/CD", ["circle ci"]),
        "prometheus": ("Monitoring", ["grafana", "observability", "monitoring", "alerting"]),
        "datadog": ("Monitoring", ["dd", "apm", "application performance monitoring"]),
        "splunk": ("Log Management", ["splunk siem", "log analysis"]),
        "nginx": ("Web Server", ["apache httpd", "load balancer", "reverse proxy"]),
        "linux": ("Operating System", ["unix", "ubuntu", "centos", "red hat", "debian"]),
        "git": ("Version Control", ["github", "gitlab", "bitbucket", "git flow"]),
        "jira": ("Tools", ["atlassian jira", "confluence", "atlassian"]),
        "agile": ("Project Management", ["scrum", "kanban", "sprint planning", "retrospective", "agile methodology"]),

        # --- TECH: Security ---
        "cybersecurity": ("Security", ["information security", "infosec", "security engineering"]),
        "penetration testing": ("Security", ["pen testing", "ethical hacking", "vulnerability assessment"]),
        "siem": ("Security", ["security information and event management", "soc analyst"]),
        "iam": ("Security", ["identity and access management", "oauth", "saml", "sso"]),
        "ssl/tls": ("Security", ["https", "certificate management", "pki"]),
        "owasp": ("Security", ["web application security", "owasp top 10"]),

        # --- NON-TECH: Healthcare & Life Sciences ---
        "registered nurse": ("Healthcare", ["rn", "registered nursing", "bsn", "msn"]),
        "patient care": ("Healthcare", ["clinical care", "patient triage", "bedside care", "patient management"]),
        "hipaa": ("Healthcare Compliance", ["hipaa compliance", "patient privacy", "phi"]),
        "electronic health records": ("Healthcare Tech", ["ehr", "emr", "epic", "cerner", "meditech", "allscripts"]),
        "clinical trials": ("Life Sciences", ["clinical research", "good clinical practice", "gcp", "phase i", "phase ii"]),
        "pharmacology": ("Healthcare", ["medication administration", "dosage calculation", "pharmacokinetics"]),
        "medical terminology": ("Healthcare", ["icd-10", "cpt coding", "medical billing", "medical coding"]),
        "radiology": ("Healthcare", ["diagnostic imaging", "mri", "ct scan", "radiography"]),
        "surgery": ("Healthcare", ["surgical procedures", "operating room", "OR nurse"]),
        "mental health": ("Healthcare", ["behavioral health", "psychiatric", "counseling", "therapy"]),
        "physical therapy": ("Healthcare", ["physiotherapy", "rehabilitation", "occupational therapy"]),
        "pathology": ("Healthcare", ["lab technician", "laboratory", "histology"]),
        "public health": ("Healthcare", ["epidemiology", "community health", "population health"]),
        "fda regulations": ("Life Sciences Compliance", ["21 cfr", "gmp", "gcp", "fda approval"]),
        "bioinformatics": ("Life Sciences", ["genomics", "proteomics", "sequencing", "ngs"]),

        # --- NON-TECH: Legal & Compliance ---
        "contract drafting": ("Legal", ["contract negotiation", "agreement drafting", "legal writing"]),
        "legal research": ("Legal", ["westlaw", "lexisnexis", "case law analysis", "legal databases"]),
        "corporate law": ("Legal", ["corporate governance", "m&a", "due diligence", "securities law"]),
        "regulatory compliance": ("Compliance", ["compliance auditing", "risk & compliance", "gdpr", "ccpa", "sox"]),
        "paralegal": ("Legal Support", ["litigation support", "legal documentation", "court filings"]),
        "intellectual property": ("Legal", ["patent law", "trademark", "copyright", "ip litigation"]),
        "employment law": ("Legal", ["labor law", "hr compliance", "ada", "fmla", "eeoc"]),
        "contract management": ("Legal", ["clm", "contract lifecycle management"]),

        # --- NON-TECH: Finance, Banking & Accounting ---
        "financial modeling": ("Finance", ["financial analysis", "forecasting", "dcf", "valuation", "lbo"]),
        "cpa": ("Accounting", ["certified public accountant", "auditing", "taxation", "tax filing"]),
        "gaap": ("Accounting Standards", ["ifrs", "financial reporting", "general ledger", "accounting standards"]),
        "bookkeeping": ("Accounting", ["accounts payable", "accounts receivable", "reconciliation", "journal entries"]),
        "quickbooks": ("Finance Tools", ["xero", "freshbooks", "accounting software"]),
        "sap": ("Enterprise Systems", ["sap erp", "sap hana", "sap fi", "sap mm", "sap s4hana"]),
        "oracle financials": ("Enterprise Systems", ["oracle erp", "oracle fusion"]),
        "risk management": ("Finance & Risk", ["credit risk", "market risk", "internal controls", "enterprise risk"]),
        "wealth management": ("Banking", ["portfolio management", "financial planning", "series 7", "cfp"]),
        "investment banking": ("Finance", ["capital markets", "equity research", "mergers acquisitions", "m&a"]),
        "trading": ("Finance", ["algorithmic trading", "derivatives", "fixed income", "equity trading"]),
        "financial planning": ("Finance", ["fp&a", "budgeting", "financial forecasting", "variance analysis"]),
        "tax accounting": ("Finance", ["tax compliance", "tax planning", "gst", "vat"]),
        "actuarial science": ("Finance", ["actuarial", "insurance modeling", "risk pricing"]),
        "anti-money laundering": ("Finance Compliance", ["aml", "kyc", "know your customer", "bsa"]),

        # --- NON-TECH: Sales, Business Development & Marketing ---
        "b2b sales": ("Sales", ["business development", "lead generation", "inside sales", "field sales", "enterprise sales"]),
        "b2c sales": ("Sales", ["retail sales", "direct sales", "consumer sales"]),
        "account management": ("Sales", ["key account management", "client relations", "customer success", "relationship management"]),
        "salesforce": ("CRM Tools", ["sfdc", "salesforce crm", "salesforce admin"]),
        "hubspot": ("CRM & Marketing", ["hubspot crm", "inbound marketing", "crm administration"]),
        "digital marketing": ("Marketing", ["seo", "sem", "google ads", "social media marketing", "ppc", "programmatic"]),
        "content strategy": ("Marketing", ["copywriting", "content marketing", "brand messaging", "editorial"]),
        "public relations": ("Marketing", ["pr", "media relations", "press releases", "brand communications"]),
        "growth hacking": ("Marketing", ["growth marketing", "funnel optimization", "conversion rate optimization", "cro"]),
        "email marketing": ("Marketing", ["mailchimp", "klaviyo", "email campaigns", "drip campaigns"]),
        "social media management": ("Marketing", ["instagram", "facebook ads", "linkedin marketing", "tiktok ads"]),
        "brand management": ("Marketing", ["brand strategy", "brand equity", "brand positioning"]),
        "market research": ("Marketing", ["consumer insights", "competitive analysis", "focus groups", "surveys"]),
        "e-commerce": ("Marketing & Sales", ["shopify", "amazon marketplace", "woocommerce", "online retail"]),

        # --- NON-TECH: Human Resources & Recruitment ---
        "talent acquisition": ("HR & Recruiting", ["technical recruiting", "executive search", "sourcing", "staffing"]),
        "hris": ("HR Tech", ["workday", "bamboohr", "zoho recruit", "successfactors", "sap hr"]),
        "employee relations": ("Human Resources", ["performance management", "conflict resolution", "hr policies", "er"]),
        "payroll": ("Human Resources", ["payroll administration", "adp", "paychex", "payroll processing"]),
        "phr": ("HR Certification", ["shrm-cp", "shrm-scp", "sphr", "cphr"]),
        "organizational development": ("Human Resources", ["od", "change management", "learning & development", "l&d"]),
        "compensation & benefits": ("Human Resources", ["c&b", "total rewards", "employee benefits", "salary benchmarking"]),
        "onboarding": ("Human Resources", ["new hire orientation", "employee lifecycle"]),
        "succession planning": ("Human Resources", ["leadership pipeline", "workforce planning"]),

        # --- NON-TECH: Supply Chain, Logistics & Manufacturing ---
        "supply chain management": ("Logistics", ["supply chain", "logistics management", "freight", "scm"]),
        "procurement": ("Supply Chain", ["purchasing", "vendor management", "strategic sourcing", "category management"]),
        "inventory control": ("Logistics", ["warehouse management", "wms", "stock control", "cycle counting"]),
        "lean six sigma": ("Operations", ["six sigma", "kaizen", "process improvement", "5s", "black belt"]),
        "sap mm": ("Supply Chain Tools", ["sap procurement", "ariba", "oracle scm"]),
        "demand forecasting": ("Supply Chain", ["demand planning", "s&op", "sales and operations planning"]),
        "transportation management": ("Logistics", ["tms", "fleet management", "last mile delivery"]),
        "quality control": ("Manufacturing", ["qc", "quality assurance", "qa", "iso 9001", "inspection"]),

        # --- NON-TECH: Construction, Architecture & Engineering ---
        "autocad": ("Engineering & Design", ["cad", "2d cad", "3d modeling", "autodesk"]),
        "revit": ("BIM & Architecture", ["building information modeling", "bim", "revit architecture"]),
        "civil engineering": ("Engineering", ["structural engineering", "site design", "geotechnical"]),
        "osha": ("Site Safety", ["osha compliance", "safety management", "site safety officer", "ehs"]),
        "leed": ("Green Building", ["leed certified", "sustainable design", "green building"]),
        "project scheduling": ("Construction", ["ms project", "primavera p6", "gantt chart", "construction schedule"]),
        "quantity surveying": ("Construction", ["cost estimation", "bill of quantities", "boq"]),
        "mechanical engineering": ("Engineering", ["hvac", "piping design", "pressure vessels"]),
        "electrical engineering": ("Engineering", ["plc", "scada", "electrical design", "power systems"]),

        # --- NON-TECH: Customer Support & Retail ---
        "customer support": ("Customer Service", ["customer service", "call center", "client support", "helpdesk"]),
        "zendesk": ("Support Tools", ["salesforce service cloud", "freshdesk", "ticketing system", "servicenow"]),
        "conflict resolution": ("Customer Service", ["de-escalation", "customer satisfaction", "csat", "nps"]),
        "store operations": ("Retail", ["retail management", "visual merchandising", "pos systems", "point of sale"]),
        "merchandising": ("Retail", ["planogram", "product display", "category management"]),

        # --- NON-TECH: Education & Training ---
        "curriculum development": ("Education", ["instructional design", "course design", "learning objectives"]),
        "lms": ("Education Tech", ["learning management system", "moodle", "canvas", "blackboard"]),
        "teaching": ("Education", ["classroom management", "lesson planning", "pedagogy"]),
        "corporate training": ("Training", ["facilitating", "training delivery", "l&d", "e-learning"]),
        "articulate": ("E-Learning Tools", ["articulate 360", "storyline", "rise"]),

        # --- NON-TECH: Real Estate & Property ---
        "property management": ("Real Estate", ["tenant relations", "lease management", "facilities management"]),
        "real estate transactions": ("Real Estate", ["title search", "escrow", "closing", "mls"]),
        "commercial real estate": ("Real Estate", ["cre", "cap rate", "noi", "lease negotiation"]),

        # --- NON-TECH: Media, Design & Creative ---
        "graphic design": ("Design", ["adobe photoshop", "adobe illustrator", "canva", "visual design"]),
        "video production": ("Media", ["video editing", "adobe premiere", "final cut pro", "after effects"]),
        "ui/ux design": ("Design", ["user experience", "user interface", "figma", "sketch", "adobe xd", "wireframing", "prototyping"]),
        "photography": ("Creative", ["photo editing", "lightroom", "studio photography"]),
        "copywriting": ("Content & Media", ["content writing", "technical writing", "blog writing", "editorial"]),
        "journalism": ("Media", ["reporting", "investigative journalism", "news writing"]),

        # --- SOFT SKILLS & MANAGEMENT ---
        "leadership": ("Soft Skill", ["team management", "people management", "mentorship", "team leadership"]),
        "communication": ("Soft Skill", ["verbal communication", "written communication", "presentation skills", "public speaking"]),
        "problem solving": ("Soft Skill", ["analytical skills", "critical thinking", "troubleshooting", "root cause analysis"]),
        "collaboration": ("Soft Skill", ["teamwork", "cross-functional collaboration", "stakeholder management"]),
        "time management": ("Soft Skill", ["prioritization", "multitasking", "deadline management"]),
        "product management": ("Product Management", ["product strategy", "product roadmap", "product owner", "po", "prm"]),
        "project management": ("Project Management", ["pmp", "prince2", "project coordination", "program management"]),
        "strategic planning": ("Management", ["strategy development", "business strategy", "long-term planning"]),
        "data-driven decision making": ("Analytics", ["data analysis", "metrics", "kpis", "reporting"]),
    }

    # Keyword indicators that suggest a skill is required (mandatory)
    MANDATORY_SIGNALS = {
        "must have", "must-have", "required", "essential", "mandatory", "minimum requirement",
        "need to have", "should have", "core requirement", "critical", "strong", "proficient",
        "experience in", "expertise in", "hands-on", "proven", "demonstrated"
    }

    # Keyword indicators that suggest a skill is nice-to-have
    PREFERRED_SIGNALS = {
        "nice to have", "nice-to-have", "preferred", "good to have", "plus", "bonus", "optional",
        "advantage", "desirable", "ideally", "helpful", "beneficial", "familiarity with"
    }

    @classmethod
    def extract_skills_from_text(cls, raw_text: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Extensive keyword extraction from raw text using Taxonomy matching, N-Gram analysis, and RegEx.
        Supports both Tech and Non-Tech domains across all industries.
        """
        if not raw_text:
            return [], []

        text_lower = raw_text.lower()

        # --- Section Detection: Split JD into Required vs Preferred zones ---
        # These patterns look for section headers in the JD text
        required_section_text = ""
        preferred_section_text = ""

        # Try to find Mandatory/Required section
        req_pattern = re.compile(
            r"(?:must[\s\-]have|required?|requirements?|qualifications?|technical skills?|"
            r"mandatory|core competenc|what you(?:'ll)? bring|what we(?:'re)? looking for|"
            r"skills? (?:and|&) experience|minimum qualifications?)[\s\S]{0,50}?:?\s*"
            r"([\s\S]+?)"
            r"(?=\n\s*\n|\Z|(?:nice[- ]to[- ]have|preferred|good[- ]to[- ]have|bonus|"
            r"benefits?|about us|compensation|salary|what (?:we offer|you(?:'ll)? get)))",
            re.IGNORECASE
        )
        req_match = req_pattern.search(text_lower)
        if req_match:
            required_section_text = req_match.group(1)

        # Try to find Nice-to-Have/Preferred section
        pref_pattern = re.compile(
            r"(?:nice[- ]to[- ]have|preferred|good[- ]to[- ]have|bonus|optional|"
            r"plus|desired|ideally|advantages?)[\s\S]{0,50}?:?\s*"
            r"([\s\S]+?)"
            r"(?=\n\s*\n|\Z|(?:benefits?|about us|compensation|salary|how to apply))",
            re.IGNORECASE
        )
        pref_match = pref_pattern.search(text_lower)
        if pref_match:
            preferred_section_text = pref_match.group(1)

        # If no section split found, treat full text as required
        if not required_section_text:
            required_section_text = text_lower

        mandatory_skills: List[Dict[str, str]] = []
        good_to_have_skills: List[Dict[str, str]] = []
        seen_skills: Set[str] = set()

        def build_skill_obj(key: str, category: str, synonyms: List[str]) -> Dict:
            display_name = key.upper() if len(key) <= 3 else key.title()
            # Fix common title-casing edge cases
            special_cases = {
                "Ai": "AI", "Nlp": "NLP", "Aws": "AWS", "Gcp": "GCP", "Sql": "SQL",
                "Api": "API", "Ehr": "EHR", "Sap": "SAP", "Crm": "CRM",
                "Erp": "ERP", "Hr": "HR", "Ui/Ux Design": "UI/UX Design",
                "Ci/Cd": "CI/CD", "Ssl/Tls": "SSL/TLS",
            }
            return {
                "name": special_cases.get(display_name, display_name),
                "category": category,
                "synonyms": synonyms,
            }

        # Step 1: Match against taxonomy
        for skill_key, (category, synonyms) in cls.SKILL_TAXONOMY.items():
            if skill_key in seen_skills:
                continue

            all_patterns = [skill_key] + synonyms
            matched_in_req = False
            matched_in_pref = False

            for pat in all_patterns:
                # Escape pattern, support multi-word
                pattern_regex = r"\b" + re.escape(pat) + r"\b"
                if required_section_text and re.search(pattern_regex, required_section_text, re.IGNORECASE):
                    matched_in_req = True
                if preferred_section_text and re.search(pattern_regex, preferred_section_text, re.IGNORECASE):
                    matched_in_pref = True

            if matched_in_req or matched_in_pref:
                seen_skills.add(skill_key)
                skill_obj = build_skill_obj(skill_key, category, synonyms)

                if matched_in_pref and not matched_in_req:
                    good_to_have_skills.append(skill_obj)
                else:
                    mandatory_skills.append(skill_obj)

        # Step 2: Dynamic N-Gram extraction for capitalized phrases not in taxonomy
        # Match multi-word capitalized phrases on the SAME LINE only: "Spring Cloud", "Clinical Trials Coordinator"
        # We process line-by-line to prevent multiline phrase captures
        cap_keywords: List[str] = []
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            matches = re.findall(
                r"\b[A-Z][a-zA-Z0-9+\-#./]*(?:\s+[A-Z][a-zA-Z0-9+\-#./]*){0,3}\b",
                line
            )
            cap_keywords.extend(matches)

        ignore_words = {
            # Stop words / articles
            "The", "And", "For", "With", "That", "This", "From", "Your", "Have", "Will",
            "Our", "Us", "Is", "Are", "Was", "Been", "Be", "Do", "Does", "Did", "Can",
            "Could", "Should", "Would", "May", "Might", "Must", "Shall", "Not", "Also",
            "New", "All", "Any", "Each", "Both", "Some", "More", "Most", "Other",
            "Including", "Such", "As", "If", "In", "At", "By", "To", "Of", "On", "An",
            "Or", "But", "A", "I", "It", "Its", "He", "She", "They", "We", "You",
            # Job posting structure words
            "Role", "Team", "Company", "Job", "Work", "About", "Senior", "Junior", "Mid",
            "Lead", "Manager", "Requirements", "Must Have", "Preferred", "Qualifications",
            "Responsibilities", "Experience", "Deep", "Familiarity", "Ability", "Knowledge",
            "Degree", "Education", "Field", "Full", "Part", "Time", "Looking", "Seeking",
            "Excellent", "Strong", "Good", "Position", "Opportunity", "Please", "Apply",
            "Equal", "Employer", "Division", "Department", "Section", "Level", "Nice",
            "Required", "Key", "Core", "Primary", "Main", "Basic", "Advanced", "Expert",
            "Minimum", "Preferred", "Desirable", "Plus", "Bonus",
            # Location / metadata words (very commonly mis-extracted)
            "Location", "Salary", "Remote", "Hybrid", "Office", "Based", "Onsite",
            "Salary Range", "Pay Range", "Compensation", "Benefits", "Equity",
            "USD", "EUR", "GBP", "INR", "CAD", "AUD",
            "Full Time", "Part Time", "Contract", "Permanent", "Freelance",
            # Time / frequency words
            "Year", "Month", "Week", "Day", "Years", "Months", "Annual", "Quarterly",
            # Generic adjectives/adverbs often appearing in JDs
            "Proven", "Demonstrated", "Exceptional", "Outstanding", "Excellent", "Strong",
            "Hands", "On", "Extensive", "Solid", "Relevant", "Related", "Significant",
            # Common verbs/adverbs that should be ignored as skills
            "Design", "Implement", "Maintain", "Create", "Manage", "Deploy", "Build", 
            "Develop", "Run", "Write", "Collaborate", "Deliver", "Deliverables", "Deliverable", 
            "Support", "Define", "Identify", "Provide", "Ensure", "Review", "Focus", "Lead", 
            "Coordinate", "Integrate", "Scale", "Optimize", "Evaluate", "Analyze", "Verify"
        }

        # Patterns for metadata that should never be a skill even if capitalized
        metadata_patterns = [
            re.compile(r'^\$[\d,]+'),           # $130,000
            re.compile(r'^\+\d'),               # +1 415...
            re.compile(r'^[A-Z]{1,3}\d'),       # NY10001, CA94107
            re.compile(r'@'),                   # email fragments
            re.compile(r'^https?://', re.I),    # URLs
            re.compile(r'^\d+[\-\+]\d+'),       # 3-5 years range
            re.compile(r'\b(LLC|Inc|Ltd|Corp|Co\.)\b', re.I),  # company suffixes
        ]

        for kw in cap_keywords:
            kw_clean = kw.strip().rstrip(".,;:!?)")
            kw_lower = kw_clean.lower()

            word_count = len(kw_clean.split())

            # Skip metadata patterns
            if any(p.search(kw_clean) for p in metadata_patterns):
                continue

            # Filter: min 3 chars, max 4 words, not a stop word, not already found
            if (3 <= len(kw_clean) <= 60 and
                    1 <= word_count <= 4 and
                    kw_clean not in ignore_words and
                    kw_lower not in seen_skills and
                    re.search(r"[a-zA-Z]", kw_clean) and
                    not kw_clean.isdigit() and
                    not re.match(r"^\d", kw_clean) and
                    # Skip if it looks like a sentence fragment (has lowercase inside)
                    not re.search(r"\s[a-z]", kw_clean)):

                seen_skills.add(kw_lower)
                skill_obj = {
                    "name": kw_clean,
                    "category": "Domain Competency",
                    "synonyms": [],
                }

                # Check if keyword appears in preferred section
                kw_in_pref = preferred_section_text and re.search(r"\b" + re.escape(kw_lower) + r"\b", preferred_section_text)
                kw_in_req = required_section_text and re.search(r"\b" + re.escape(kw_lower) + r"\b", required_section_text)

                if kw_in_pref and not kw_in_req:
                    good_to_have_skills.append(skill_obj)
                else:
                    mandatory_skills.append(skill_obj)

        return mandatory_skills, good_to_have_skills
