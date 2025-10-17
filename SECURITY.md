# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in the EleutherIA Ancient Free Will Database, please report it to us as described below.

### How to Report

**For Data Security Issues:**
- Email: romain.girardi@univ-cotedazur.fr
- Subject: [SECURITY] EleutherIA Database Vulnerability
- Include: Description of the vulnerability and steps to reproduce

**For Technical Security Issues:**
- Email: romain.girardi@univ-cotedazur.fr
- Subject: [SECURITY] Technical Vulnerability
- Include: Description, impact assessment, and suggested fixes

### What to Include

Please include the following information in your report:

1. **Vulnerability Type:**
   - Data integrity issue
   - Schema validation bypass
   - Character encoding vulnerability
   - Access control issue
   - Other (please specify)

2. **Description:**
   - Clear description of the vulnerability
   - Steps to reproduce the issue
   - Expected vs. actual behavior

3. **Impact Assessment:**
   - Potential impact on data integrity
   - Risk level (Low/Medium/High/Critical)
   - Affected components

4. **Suggested Fix:**
   - If you have suggestions for fixing the issue
   - Any relevant references or documentation

### Response Timeline

- **Acknowledgment:** Within 48 hours
- **Initial Assessment:** Within 1 week
- **Resolution:** Depends on severity and complexity
- **Public Disclosure:** After fix is available

### Security Considerations

#### Data Integrity
- All database content is verified against ancient sources
- Modern scholarship references are validated
- No hallucinated or fabricated content is permitted
- Greek/Latin character encoding is strictly enforced

#### Schema Validation
- JSON Schema validation prevents malformed data
- Required fields are enforced
- Data types are strictly validated
- Edge references are verified against existing nodes

#### Access Control
- Database is publicly accessible under CC BY 4.0 license
- No authentication required for read access
- All changes are tracked through version control
- Pull requests require review before merging

#### Character Encoding
- UTF-8 encoding is required for all text fields
- Greek and Latin characters are preserved
- No character substitution or corruption is tolerated
- Validation scripts check encoding integrity

### Known Security Considerations

#### Data Validation
- The database contains historical and philosophical content
- All claims must be backed by source citations
- No modern political or controversial content
- Academic standards are maintained

#### Technical Security
- Database is static JSON format (no executable code)
- No server-side processing or dynamic content
- All scripts are open source and auditable
- Dependencies are regularly updated

### Best Practices

#### For Users
- Always validate database integrity before use
- Report any suspicious or incorrect content
- Use official releases only
- Verify checksums when available

#### For Contributors
- Follow established coding standards
- Include comprehensive tests
- Validate all data changes
- Document security considerations

### Contact Information

**Primary Contact:**
- Name: Romain Girardi
- Email: romain.girardi@univ-cotedazur.fr
- Institution: Université Côte d'Azur, CEPAM

**Institutional Support:**
- Université Côte d'Azur, CEPAM
- Université de Genève, Faculté de Théologie Jean Calvin

### Acknowledgments

We appreciate the security research community's efforts to help keep EleutherIA secure. Responsible disclosure helps us maintain the integrity and reliability of the database for the academic community.

---

**Last Updated:** October 17, 2025  
**Version:** 1.0.0  
**Maintained by:** Romain Girardi (romain.girardi@univ-cotedazur.fr)
