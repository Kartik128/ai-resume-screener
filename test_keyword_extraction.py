import sys
sys.path.insert(0, "backend")

from app.services.skill_taxonomy_service import SkillTaxonomyService

sample_jd = """
We are hiring a Senior Full Stack Engineer.
Must Have Requirements:
- 5+ years of experience with Java, Spring Boot, and Microservices.
- Experience with Kubernetes, Docker, AWS, and CI/CD pipelines.
- Deep knowledge of PostgreSQL, Redis, Kafka, and System Design.

Preferred Qualifications:
- Familiarity with React, TypeScript, GraphQL, and Tailwind CSS.
- Financial Modeling and Risk Management background is a plus.
"""

mand, good = SkillTaxonomyService.extract_skills_from_text(sample_jd)

print("=== EXTRACTED MANDATORY SKILLS ===")
for m in mand:
    print(f" - [{m['category']}] {m['name']}")

print("\n=== EXTRACTED GOOD TO HAVE SKILLS ===")
for g in good:
    print(f" - [{g['category']}] {g['name']}")
