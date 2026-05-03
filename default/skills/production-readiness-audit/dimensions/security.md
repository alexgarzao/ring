# Audit Dimensions: Category B — Security & Access Control

These are the 9 (+1 conditional) explorer agent prompts for Security dimensions.
Agent 33 (Multi-Tenant) is CONDITIONAL — only dispatch if MULTI_TENANT=true.
Inject Ring standards and detected stack before dispatching.

### Agent 6: Auth Protection Auditor

```prompt
Audit authentication and authorization implementation for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Access Manager Integration" section from security.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/auth/*.go`, `**/middleware*.go`, `**/routes.go`
- Keywords: `Authorize`, `protected`, `JWT`, `tenant`, `ExtractToken`
- Standards-specific: `AccessManager`, `lib-auth`, `ProtectedGroup`

**Reference Implementation (GOOD):**
```go
// Protected route group
protected := func(resource, action string) fiber.Router {
    return auth.ProtectedGroup(api, authClient, tenantExtractor, resource, action)
}

// All routes use protected
protected("contexts", "create").Post("/v1/config/contexts", handler.Create)

// JWT validation
func parseTokenClaims(tokenString string, secret []byte) (jwt.MapClaims, error) {
    parser := jwt.NewParser(jwt.WithValidMethods(validSigningMethods))
    token, err := parser.ParseWithClaims(...)
    if err != nil || !token.Valid {
        return nil, ErrInvalidToken
    }
    // Check expiration
    if exp, ok := claims["exp"].(float64); ok {
        if time.Now().Unix() > int64(exp) {
            return nil, ErrTokenExpired
        }
    }
    return claims, nil
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) All routes protected via Access Manager integration per security.md
2. (HARD GATE) lib-auth used for JWT validation (not custom JWT parsing)
3. Resource/action authorization granularity per Ring access control model
4. Token expiration enforcement
5. Tenant extraction from JWT claims
6. Auth bypass for health/ready endpoints only

**Severity Ratings:**
- CRITICAL: Unprotected data endpoints (HARD GATE violation per Ring standards)
- CRITICAL: JWT parsed but not validated
- CRITICAL: HARD GATE violation — not using lib-auth for access management
- HIGH: Missing token expiration check
- HIGH: Tenant claims not enforced
- MEDIUM: Overly broad permissions
- LOW: Missing fine-grained actions

**Output Format:**
```
## Auth Protection Audit Findings

### Summary
- Protected routes: X/Y
- JWT validation: Complete/Partial/Missing
- Tenant enforcement: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 7: IDOR & Access Control Auditor

```prompt
Audit IDOR (Insecure Direct Object Reference) protection for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Search Patterns:**
- Files: `**/verifier*.go`, `**/handlers.go`, `**/context.go`
- Keywords: `VerifyOwnership`, `tenantID`, `contextID`, `ParseAndVerify`

**Reference Implementation (GOOD):**
```go
// 4-layer IDOR protection
func ParseAndVerifyContextParam(fiberCtx *fiber.Ctx, verifier ContextOwnershipVerifier) (uuid.UUID, uuid.UUID, error) {
    // 1. UUID format validation
    contextID, err := uuid.Parse(fiberCtx.Params("contextId"))
    if err != nil {
        return uuid.Nil, uuid.Nil, ErrInvalidID
    }

    // 2. Extract tenant from auth context (cannot be spoofed)
    tenantID := auth.GetTenantID(ctx)

    // 3. Database query filtered by tenant
    // 4. Post-query ownership verification
    if err := verifier.VerifyOwnership(ctx, tenantID, contextID); err != nil {
        return uuid.Nil, uuid.Nil, err
    }
    return contextID, tenantID, nil
}

// Verifier implementation
func (v *verifier) VerifyOwnership(ctx context.Context, tenantID, resourceID uuid.UUID) error {
    resource, err := v.query.Get(ctx, tenantID, resourceID)  // Query WITH tenant filter
    if errors.Is(err, sql.ErrNoRows) {
        return ErrNotFound
    }
    if resource.TenantID != tenantID {  // Double-check ownership
        return ErrNotOwned
    }
    return nil
}
```

**Reference Implementation (BAD):**
```go
// BAD: No ownership verification
func GetResource(c *fiber.Ctx) error {
    id := c.Params("id")
    resource, err := repo.FindByID(ctx, id)  // No tenant filter!
    return c.JSON(resource)
}
```

**Check For:**
1. All resource access verifies ownership
2. Tenant ID from JWT context (not request params)
3. Database queries include tenant filter
4. Post-query ownership double-check
5. UUID validation before database lookup
6. Consistent verifier pattern across modules

**Severity Ratings:**
- CRITICAL: Resource access without ownership check
- CRITICAL: Tenant ID from user input (not JWT)
- HIGH: Missing post-query ownership verification
- MEDIUM: Inconsistent verifier implementation
- LOW: Missing UUID format validation

**Output Format:**
```
## IDOR Protection Audit Findings

### Summary
- Modules with verifiers: X/Y
- Multi-tenant filtered queries: X/Y
- Post-query verification: X/Y

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 8: SQL Safety Auditor

```prompt
Audit SQL injection prevention for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Search Patterns:**
- Files: `**/*.postgresql.go`, `**/repository/*.go`, `**/*_repo.go`
- Keywords: `ExecContext`, `QueryContext`, `Exec(`, `Query(`, `$1`, `$2`
- Also search for: String concatenation in SQL: `"SELECT.*" +`, `fmt.Sprintf.*SELECT`

**Reference Implementation (GOOD):**
```go
// Parameterized queries
query := `INSERT INTO resources (id, name, tenant_id) VALUES ($1, $2, $3)`
_, err = tx.ExecContext(ctx, query, id, name, tenantID)

// SQL identifier escaping for dynamic schemas
func QuoteIdentifier(identifier string) string {
    return "\"" + strings.ReplaceAll(identifier, "\"", "\"\"") + "\""
}
schemaQuery := "SET LOCAL search_path TO " + QuoteIdentifier(tenantID)

// Query builder (Squirrel)
query := sq.Select("*").From("resources").Where(sq.Eq{"tenant_id": tenantID})
```

**Reference Implementation (BAD):**
```go
// BAD: String concatenation
query := "SELECT * FROM users WHERE name = '" + name + "'"

// BAD: fmt.Sprintf for values
query := fmt.Sprintf("SELECT * FROM users WHERE id = '%s'", id)

// BAD: Unescaped identifier
query := "SET search_path TO " + tenantID  // SQL injection via tenant
```

**Check For:**
1. All queries use parameterized statements ($1, $2, ...)
2. No string concatenation in SQL queries
3. Dynamic identifiers properly escaped (QuoteIdentifier)
4. Query builders used for complex WHERE clauses
5. No raw SQL with user input

**Severity Ratings:**
- CRITICAL: String concatenation with user input
- CRITICAL: fmt.Sprintf with user values
- HIGH: Unescaped dynamic identifiers
- MEDIUM: Raw SQL where builder would be safer
- LOW: Inconsistent query patterns

**Output Format:**
```
## SQL Safety Audit Findings

### Summary
- Parameterized queries: X/Y
- String concatenation risks: Z
- Identifier escaping: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 9: Input Validation Auditor

```prompt
Audit input validation patterns for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Frameworks & Libraries" section from core.md — specifically go-playground/validator/v10 reference}
---END STANDARDS---

**Search Patterns:**
- Files: `**/dto.go`, `**/handlers.go`, `**/value_objects/*.go`
- Keywords: `validate:`, `BodyParser`, `IsValid()`, `Parse`, `required`
- Standards-specific: `validator/v10`, `go-playground/validator`

**Reference Implementation (GOOD):**
```go
// DTO with validation tags
type CreateRequest struct {
    Name   string `json:"name" validate:"required,min=1,max=255"`
    Type   string `json:"type" validate:"required,oneof=TYPE_A TYPE_B"`
    Amount int    `json:"amount" validate:"gte=0,lte=1000000"`
}

// Handler with body parsing error handling
func (h *Handler) Create(c *fiber.Ctx) error {
    var payload CreateRequest
    if err := c.BodyParser(&payload); err != nil {
        return badRequest(c, span, logger, "invalid request body", err)
    }
    // Validate struct
    if err := h.validator.Struct(payload); err != nil {
        return badRequest(c, span, logger, "validation failed", err)
    }
    ...
}

// Value object with domain validation
func (vo ValueObject) IsValid() bool {
    if vo.value == "" || len(vo.value) > maxLength {
        return false
    }
    return validPattern.MatchString(vo.value)
}
```

**Reference Implementation (BAD):**
```go
// BAD: No validation tags
type Request struct {
    Name string `json:"name"`  // No validation!
}

// BAD: Ignoring body parse error
payload := Request{}
c.BodyParser(&payload)  // Error ignored!

// BAD: No bounds checking
amount := c.QueryInt("amount")  // Could be negative or huge
```

**Check Against Ring Standards For:**
1. (HARD GATE) go-playground/validator/v10 used for struct validation per Ring core.md
2. (HARD GATE) All DTOs have validate: tags on required fields
3. BodyParser errors are handled (not ignored)
4. Query/path params validated before use
5. Numeric bounds enforced (min/max)
6. String length limits enforced
7. Enum values constrained (oneof=)
8. Value objects have IsValid() methods
9. File upload size/type validation

**Severity Ratings:**
- CRITICAL: BodyParser errors ignored
- CRITICAL: HARD GATE violation — not using go-playground/validator/v10 per Ring standards
- HIGH: No validation on user input DTOs
- HIGH: Unbounded numeric inputs
- MEDIUM: Missing string length limits
- LOW: Value objects without IsValid()

**Output Format:**
```
## Input Validation Audit Findings

### Summary
- DTOs with validation tags: X/Y
- BodyParser error handling: X/Y
- Value objects with IsValid: X/Y

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 37: Secret Scanning Auditor

```prompt
Audit the codebase for hardcoded secrets, credentials, API keys, tokens, and sensitive data exposure for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: Secret scanning patterns — no dedicated standards file; patterns derived from industry secret detection rules (GitHub secret scanning, truffleHog, gitleaks)}
---END STANDARDS---

**Search Patterns:**
- All source files: `**/*.go`, `**/*.ts`, `**/*.tsx`, `**/*.js`, `**/*.jsx`, `**/*.py`, `**/*.java`
- Configuration files: `**/*.yaml`, `**/*.yml`, `**/*.json`, `**/*.toml`, `**/*.ini`, `**/*.conf`, `**/*.cfg`
- Environment files: `**/*.env`, `**/*.env.*`, `.env.local`, `.env.production`
- Key/certificate files: `**/*.pem`, `**/*.key`, `**/*.p12`, `**/*.pfx`, `**/*.crt`, `**/*.cer`
- Docker/CI: `**/Dockerfile*`, `**/.github/workflows/*.yml`, `**/docker-compose*.yml`, `**/.gitlab-ci.yml`
- Keywords (credentials): `password`, `passwd`, `pwd`, `secret`, `api_key`, `apikey`, `api-key`, `token`, `auth_token`, `access_token`, `private_key`, `credential`
- Keywords (connection): `connection_string`, `conn_str`, `database_url`, `redis_url`, `mongodb_uri`, `dsn`
- Keywords (cloud): `AKIA`, `ASIA` (AWS), `AIza` (GCP), `ghp_`, `gho_`, `ghu_` (GitHub), `sk-` (OpenAI/Stripe), `xoxb-`, `xoxp-` (Slack)
- Patterns (high-entropy): Base64 strings > 20 chars, hex strings > 32 chars, `eyJ` (JWT prefix)
- Patterns (private keys): `-----BEGIN.*PRIVATE KEY-----`, `-----BEGIN RSA`, `-----BEGIN EC`, `-----BEGIN OPENSSH`

**Secret Detection Patterns to Check:**

| Pattern | Risk Level | What to Look For |
|---------|:----------:|------------------|
| Private keys in source | CRITICAL | `-----BEGIN RSA PRIVATE KEY-----` or similar PEM blocks committed to repo |
| Cloud provider credentials | CRITICAL | AWS access keys (`AKIA...`), GCP service account JSON, Azure client secrets in source |
| Database connection strings with passwords | CRITICAL | `postgres://user:password@`, `mongodb+srv://user:pass@`, `mysql://root:pass@` |
| API keys/tokens hardcoded | HIGH | `const API_KEY = "sk-..."`, `token: "ghp_..."`, inline bearer tokens |
| .env files in version control | HIGH | `.env`, `.env.production` tracked by git (not in .gitignore) |
| JWT tokens hardcoded | HIGH | Strings starting with `eyJ` (base64-encoded JSON header) in source code |
| Secrets in CI/CD config | HIGH | Plaintext secrets in GitHub Actions workflows, Docker compose, or CI config |
| Secrets in config files without encryption | MEDIUM | Passwords or tokens in YAML/JSON/TOML config files not using vault references |
| Secrets in comments or documentation | MEDIUM | Example credentials in comments that are actually real, or TODO with temp credentials |
| Secrets in test fixtures | MEDIUM | Test files containing what appear to be real credentials (not obviously fake) |
| Weak secret references | LOW | Hardcoded default passwords like `password123`, `admin`, `changeme` in non-test code |
| Example credentials resembling real ones | LOW | Test/example values that follow real credential formats (could confuse scanning tools) |

**Gitignore Verification (MANDATORY — do not skip):**
1. **Check .gitignore exists** at repository root
2. **Verify .env exclusion**: `.env`, `.env.*`, `.env.local`, `.env.production` MUST be in .gitignore
3. **Verify key file exclusion**: `*.pem`, `*.key`, `*.p12`, `*.pfx` SHOULD be in .gitignore
4. **Check for tracked .env files**: `git ls-files '*.env*'` — any results are HIGH severity findings
5. **Check for tracked key files**: `git ls-files '*.pem' '*.key'` — any results are CRITICAL

**Reference Implementation (GOOD):**
```go
// GOOD: Secrets from environment variables
dbURL := os.Getenv("DATABASE_URL")
if dbURL == "" {
    log.Fatal("DATABASE_URL environment variable is required")
}

// GOOD: API key from environment
apiKey := os.Getenv("EXTERNAL_API_KEY")

// GOOD: Secret from vault/secret manager
secret, err := vault.ReadSecret(ctx, "secret/data/myapp/api-key")
if err != nil {
    return fmt.Errorf("failed to read secret: %w", err)
}
```

```typescript
// GOOD: Secrets from environment
const dbUrl = process.env.DATABASE_URL;
if (!dbUrl) {
  throw new Error('DATABASE_URL environment variable is required');
}

// GOOD: Secret from config service
const apiKey = await configService.getSecret('EXTERNAL_API_KEY');
```

```yaml
# GOOD: .gitignore includes secret files
.env
.env.*
.env.local
.env.production
*.pem
*.key
*.p12
*.pfx
credentials.json
```

**Reference Implementation (BAD):**
```go
// BAD: Hardcoded API key
const APIKey = "sk-proj-abc123xyz789..."

// BAD: Hardcoded database connection with password
const DatabaseURL = "postgres://admin:SuperSecret123@db.example.com:5432/production"

// BAD: Hardcoded AWS credentials
const AWSAccessKey = "AKIAIOSFODNN7EXAMPLE"
const AWSSecretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

```typescript
// BAD: Inline token
const headers = {
  Authorization: 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
};

// BAD: Hardcoded connection string
const mongoUri = 'mongodb+srv://admin:P@ssw0rd@cluster0.example.mongodb.net/prod';
```

```yaml
# BAD: Secrets in docker-compose.yml
services:
  app:
    environment:
      - DB_PASSWORD=MySecretPassword123
      - API_KEY=sk-live-abc123
```

**Check Against Standards For:**
1. (CRITICAL) No private keys (RSA, SSH, TLS) committed to source control
2. (CRITICAL) No cloud provider credentials (AWS access keys, GCP service account JSON, Azure secrets) in source
3. (CRITICAL) No database connection strings with embedded passwords in source code
4. (HIGH) No API keys or tokens hardcoded in source files (MUST come from environment or secret manager)
5. (HIGH) .env files are in .gitignore and not tracked by git
6. (HIGH) No plaintext secrets in CI/CD configuration files
7. (HIGH) No hardcoded JWT tokens in source code
8. (MEDIUM) Configuration files use vault references or environment variable substitution for secrets
9. (MEDIUM) No real-looking credentials in comments, documentation, or TODO items
10. (MEDIUM) Test fixtures use obviously fake credentials (e.g., `test-key-not-real`, not `sk-abc123`)
11. (LOW) No default passwords like `password`, `admin`, `changeme` in non-test code
12. (LOW) Example credentials in documentation are clearly marked as fake

**Severity Ratings:**
- CRITICAL: Private keys committed to repo (full compromise), cloud provider credentials in source (account takeover), database connection strings with passwords (data breach)
- HIGH: API keys/tokens hardcoded (service compromise), .env tracked by git (secret exposure on clone), secrets in CI/CD config (pipeline compromise), hardcoded JWT tokens (authentication bypass)
- MEDIUM: Secrets in config files without encryption (exposure if config leaked), real-looking credentials in comments (confusion, potential real secrets), test fixtures with real-format secrets (may be actual secrets)
- LOW: Default/weak passwords in non-test code (brute force risk), example credentials resembling real format (scanner noise)

**Output Format:**
```
## Secret Scanning Audit Findings

### Summary
- Files scanned: X
- Secrets found: Y total (Z unique)
- .gitignore coverage: Adequate/Inadequate
- .env files tracked: X (MUST be 0)
- Key/certificate files tracked: X (MUST be 0)
- Secret management approach: {env vars / vault / config service / mixed / none detected}

### Critical Issues
[file:line] - Description (type: {secret type})
  Evidence: {redacted snippet showing pattern, NOT the actual secret}
  Impact: {what an attacker could do with this secret}
  Fix: Move to environment variable or secret manager; rotate immediately

### High Issues
[file:line] - Description (type: {secret type})
  Evidence: {redacted snippet}
  Fix: {specific remediation}

### Medium Issues
[file:line] - Description

### Low Issues
[file:line] - Description

### .gitignore Analysis
- .env patterns: {listed / missing}
- Key file patterns: {listed / missing}
- Tracked secret files: {list or "none"}

### Recommendations
1. ...

### IMPORTANT: Secret Rotation Notice
{If any CRITICAL or HIGH secrets are found, include this notice:}
WARNING: Any secrets found in source code MUST be considered compromised.
Rotate all affected credentials IMMEDIATELY — removing from code is not sufficient.
```
```

### Agent 41: Data Encryption at Rest Auditor

```prompt
Audit data encryption at rest, key management, and sensitive data protection for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: Data encryption patterns — no dedicated standards file; patterns derived from security best practices and OWASP guidelines}
---END STANDARDS---

**Search Patterns:**
- Go files: `**/*.go` — search for encryption libraries, hashing functions, sensitive field handling, key management
- TypeScript files: `**/*.ts`, `**/*.tsx` — search for crypto modules, encryption utilities, password hashing
- Config files: `**/*.yaml`, `**/*.yml`, `**/*.env*`, `**/docker-compose*` — search for encryption keys, database encryption settings
- SQL/Migration files: `**/*.sql`, `**/migrations/**` — search for sensitive columns, pgcrypto, encryption extensions
- Keywords (Go): `crypto/aes`, `crypto/cipher`, `bcrypt`, `scrypt`, `argon2`, `aes.NewCipher`, `gcm`, `Seal`, `Open`, `GenerateFromPassword`, `CompareHashAndPassword`
- Keywords (TS): `crypto`, `createCipheriv`, `createDecipheriv`, `node-forge`, `bcrypt`, `argon2`, `scrypt`, `pbkdf2`
- Keywords (DB): `pgcrypto`, `encrypt`, `decrypt`, `gen_salt`, `crypt`, `ENCRYPTED`, `BYTEA`
- Keywords (Config): `ENCRYPTION_KEY`, `MASTER_KEY`, `KMS`, `vault`, `SECRET_KEY`, `CIPHER`

**Sensitive Data Patterns to Identify:**

| Data Type | Identifiers | Required Protection |
|-----------|-------------|---------------------|
| Passwords | `password`, `passwd`, `pass`, `secret` | Hashed with bcrypt/argon2/scrypt (NEVER plaintext, NEVER reversible encryption) |
| Credit cards | `credit_card`, `card_number`, `pan`, `cc_num` | Field-level encryption (AES-256-GCM), masked in logs |
| Bank accounts | `bank_account`, `account_number`, `iban`, `routing` | Field-level encryption |
| SSN / Tax IDs | `ssn`, `tax_id`, `national_id`, `social_security` | Field-level encryption |
| API keys / tokens | `api_key`, `token`, `secret_key`, `access_key` | Encrypted at rest, never in source |
| PII (general) | `email`, `phone`, `address`, `date_of_birth` | Encryption recommended for regulated environments |

**Encryption Safety Methodology (MANDATORY — do not skip):**
1. **Inventory sensitive fields**: Scan models, database schemas, and API payloads for sensitive data types
2. **Check password hashing**: Verify all password storage uses bcrypt, argon2, or scrypt — NEVER plaintext or reversible encryption
3. **Check field encryption**: Verify financial and identity data uses AES-256-GCM or equivalent field-level encryption
4. **Check key management**: Verify encryption keys come from KMS, Vault, or secure secret store — NOT from source code or .env files
5. **Check backups**: Verify database backup processes include encryption
6. **Check algorithm strength**: Flag use of MD5, SHA1, DES, RC4, or other deprecated algorithms

**Go Encryption Patterns to Check:**

| Pattern | Risk Level | What to Look For |
|---------|:----------:|------------------|
| Plaintext passwords | CRITICAL | `password` field stored as `string` in DB without hashing |
| Weak hash for passwords | CRITICAL | `md5.Sum`, `sha1.Sum`, `sha256.Sum` used for password hashing (use bcrypt/argon2 instead) |
| Unencrypted financial data | CRITICAL | Credit card, bank account stored as plain `string` in DB |
| Keys in source | HIGH | `ENCRYPTION_KEY`, `MASTER_KEY` hardcoded in Go files or committed .env |
| No key rotation | MEDIUM | Single encryption key with no rotation mechanism or key versioning |
| Weak algorithm | MEDIUM | DES, RC4, AES-ECB (use AES-GCM), MD5/SHA1 for integrity |
| Unencrypted backups | HIGH | Backup commands/scripts without encryption flag |

**TypeScript Encryption Patterns to Check:**

| Pattern | Risk Level | What to Look For |
|---------|:----------:|------------------|
| Plaintext passwords | CRITICAL | Password stored/compared as plain string without hashing |
| Weak hash for passwords | CRITICAL | `crypto.createHash('md5')` or `crypto.createHash('sha1')` for passwords |
| Unencrypted sensitive data | CRITICAL | PII or financial data stored without encryption |
| Keys in source | HIGH | Encryption keys hardcoded in TypeScript files |
| No key rotation | MEDIUM | Static encryption key with no versioning |
| Weak algorithm | MEDIUM | `createCipheriv('des', ...)`, `createCipheriv('aes-128-ecb', ...)` |

**Reference Implementation (GOOD — Go):**
```go
// GOOD: Password hashing with bcrypt
import "golang.org/x/crypto/bcrypt"

func HashPassword(password string) (string, error) {
    hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    if err != nil {
        return "", fmt.Errorf("hashing password: %w", err)
    }
    return string(hash), nil
}

func VerifyPassword(hash, password string) error {
    return bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
}

// GOOD: AES-256-GCM field encryption with key from Vault
func EncryptField(plaintext []byte, key []byte) ([]byte, error) {
    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, err
    }
    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }
    nonce := make([]byte, gcm.NonceSize())
    if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
        return nil, err
    }
    return gcm.Seal(nonce, nonce, plaintext, nil), nil
}

// GOOD: Key from Vault/KMS
func GetEncryptionKey(ctx context.Context) ([]byte, error) {
    secret, err := vaultClient.Logical().Read("secret/data/encryption-key")
    if err != nil {
        return nil, fmt.Errorf("reading encryption key from vault: %w", err)
    }
    return base64.StdEncoding.DecodeString(secret.Data["key"].(string))
}
```

**Reference Implementation (BAD — Go):**
```go
// BAD: Plaintext password storage
type User struct {
    Email    string `db:"email"`
    Password string `db:"password"` // stored as plain text!
}

// BAD: MD5 for password hashing — trivially crackable
func HashPassword(password string) string {
    hash := md5.Sum([]byte(password))
    return hex.EncodeToString(hash[:])
}

// BAD: Encryption key hardcoded in source
var encryptionKey = []byte("my-super-secret-key-1234567890ab")

// BAD: AES-ECB mode — deterministic, leaks patterns
block, _ := aes.NewCipher(key)
block.Encrypt(ciphertext, plaintext) // ECB mode — do NOT use
```

**Reference Implementation (GOOD — TypeScript):**
```typescript
// GOOD: Password hashing with argon2
import argon2 from 'argon2';

async function hashPassword(password: string): Promise<string> {
    return argon2.hash(password, { type: argon2.argon2id });
}

async function verifyPassword(hash: string, password: string): Promise<boolean> {
    return argon2.verify(hash, password);
}

// GOOD: AES-256-GCM field encryption
import { createCipheriv, createDecipheriv, randomBytes } from 'crypto';

function encryptField(plaintext: string, key: Buffer): string {
    const iv = randomBytes(16);
    const cipher = createCipheriv('aes-256-gcm', key, iv);
    const encrypted = Buffer.concat([cipher.update(plaintext, 'utf8'), cipher.final()]);
    const tag = cipher.getAuthTag();
    return Buffer.concat([iv, tag, encrypted]).toString('base64');
}
```

**Reference Implementation (BAD — TypeScript):**
```typescript
// BAD: Plaintext password comparison
async function login(email: string, password: string): Promise<User> {
    const user = await db.users.findByEmail(email);
    if (user.password !== password) throw new Error('Invalid'); // plaintext!
    return user;
}

// BAD: MD5 for hashing
import { createHash } from 'crypto';
const hash = createHash('md5').update(password).digest('hex');

// BAD: Encryption key in source
const ENCRYPTION_KEY = 'hardcoded-secret-key-do-not-do-this';
```

**Check Against Standards For:**
1. (CRITICAL) All passwords are hashed with bcrypt, argon2, or scrypt — never plaintext or reversible encryption
2. (CRITICAL) Credit card and financial data is encrypted at rest with AES-256-GCM or equivalent
3. (CRITICAL) No weak hashing algorithms (MD5, SHA1) used for passwords or security-sensitive data
4. (HIGH) PII (SSN, tax ID, national ID) is encrypted with field-level encryption
5. (HIGH) Encryption keys are stored in KMS, Vault, or secure secret store — not in source code or .env files
6. (HIGH) Database backups are encrypted
7. (MEDIUM) No deprecated/weak encryption algorithms (DES, RC4, AES-ECB)
8. (MEDIUM) Key rotation mechanism exists (key versioning, re-encryption strategy)
9. (LOW) Non-sensitive data is not unnecessarily encrypted (performance overhead)

**Severity Ratings:**
- CRITICAL: Plaintext password storage, credit card/financial data stored unencrypted, weak hash algorithms (MD5/SHA1) for passwords
- HIGH: PII stored without field-level encryption, encryption keys in source code or .env, unencrypted backups, no key management strategy
- MEDIUM: Weak encryption algorithms (DES, RC4, AES-ECB), no key rotation mechanism, SHA256 used for password hashing (use bcrypt/argon2 instead)
- LOW: Non-sensitive data encrypted unnecessarily (performance overhead), missing encryption documentation

**Output Format:**
```
## Data Encryption at Rest Audit Findings

### Summary
- Sensitive data types found: {password, credit card, SSN, ...}
- Password hashing: {bcrypt / argon2 / scrypt / MD5 / SHA1 / plaintext}
- Field encryption: {AES-256-GCM / AES-ECB / none}
- Key management: {Vault / KMS / env var / hardcoded / none}
- Key rotation: Yes/No
- Backup encryption: Yes/No/Unknown

### Critical Issues
[file:line] - Description (data type: {type}, current protection: {none/weak})

### High Issues
[file:line] - Description (data type: {type})

### Medium Issues
[file:line] - Description

### Low Issues
[file:line] - Description

### Sensitive Data Inventory
| Field/Column | Data Type | Location | Current Protection | Required Protection | Gap |
|-------------|-----------|----------|-------------------|--------------------|----|
| ... | ... | ... | ... | ... | ... |

### Recommendations
1. ...
```
```

### Agent 43: Rate Limiting Auditor

```prompt
Audit rate limiting implementation across the codebase for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: security.md § Rate Limiting (MANDATORY)}
---END STANDARDS---

**Search Patterns:**
- Go files: `**/*.go` — search for rate limiting middleware, limiter configuration, Redis storage for rate limits
- Config files: `**/*.env*`, `**/docker-compose*`, `**/config*.go` — search for RATE_LIMIT env vars
- Middleware files: `**/middleware/**`, `**/bootstrap/**` — search for limiter registration
- Keywords (Go): `limiter`, `ratelimit`, `rate_limit`, `RateLimit`, `RATE_LIMIT`, `fiber/middleware/limiter`, `MaxRequests`, `Expiration`, `KeyGenerator`, `LimitReached`, `429`, `Retry-After`
- Keywords (Config): `RATE_LIMIT_ENABLED`, `RATE_LIMIT_MAX`, `RATE_LIMIT_EXPIRY_SEC`, `EXPORT_RATE_LIMIT`, `DISPATCH_RATE_LIMIT`

**Rate Limiting Patterns to Check:**

| Pattern | Risk Level | What to Look For |
|---------|:----------:|------------------|
| No rate limiting at all | CRITICAL | No limiter middleware registered on any route |
| Single-tier only | HIGH | Only global rate limit, no export/dispatch tiers |
| In-memory storage only | HIGH | `fiber.Storage` not backed by Redis — rate limits not shared across instances |
| Hardcoded limits | MEDIUM | Rate limit values hardcoded in code instead of env vars |
| No key generation strategy | HIGH | Default key generator (IP only) — no UserID or TenantID+IP |
| Rate limiting disabled in production | CRITICAL | `RATE_LIMIT_ENABLED=false` with no production override |
| No 429 response with Retry-After | MEDIUM | Rate limit exceeded but no `Retry-After` header in response |
| No graceful degradation | HIGH | Redis unavailable causes request failures instead of fallback to in-memory |

**Three-tier Strategy Verification (MANDATORY — do not skip):**
1. **Global tier**: Verify a general rate limiter exists on all protected routes (default: 100 req/60s)
2. **Export tier**: Verify resource-intensive endpoints (exports, bulk ops) have a stricter limiter (default: 10 req/60s)
3. **Dispatch tier**: Verify external integration endpoints (webhooks, external calls) have their own limiter (default: 50 req/60s)

**Redis Storage Verification (MANDATORY — do not skip):**
1. **Storage implementation**: Verify rate limiter uses Redis-backed storage implementing `fiber.Storage` interface
2. **Key prefix**: Verify rate limit keys use `ratelimit:` prefix for namespace isolation
3. **Sentinel errors**: Verify Redis operations use sentinel errors (not `fmt.Errorf`)
4. **Graceful degradation**: Verify fallback behavior when Redis is unavailable

**Production Safety Verification (MANDATORY — do not skip):**
1. **Force-enable in production**: Verify rate limiting cannot be disabled when `ENV_NAME=production`
2. **Key generation**: Verify key generator uses UserID > TenantID+IP > IP priority
3. **Configuration via env vars**: Verify all limits are configurable via environment variables

**Reference Implementation (GOOD — Go):**
```go
// GOOD: Three-tier rate limiting with Redis storage
rateLimitStorage := ratelimit.NewRedisStorage(redisConn)

// Global limiter
app.Use(limiter.New(limiter.Config{
    Max:        cfg.RateLimit.Max,
    Expiration: time.Duration(cfg.RateLimit.ExpirySec) * time.Second,
    Storage:    rateLimitStorage,
    KeyGenerator: func(c *fiber.Ctx) string {
        // UserID > TenantID+IP > IP
        if uid := c.Locals("userID"); uid != nil {
            return fmt.Sprintf("user:%v", uid)
        }
        if tid := c.Locals("tenantID"); tid != nil {
            return fmt.Sprintf("tenant:%v:ip:%s", tid, c.IP())
        }
        return c.IP()
    },
}))
```

**Reference Implementation (BAD — Go):**
```go
// BAD: No rate limiting at all — DoS vulnerable
app.Get("/api/v1/exports", exportHandler)

// BAD: Hardcoded limits, no Redis storage
app.Use(limiter.New(limiter.Config{
    Max:        100,           // hardcoded
    Expiration: time.Minute,   // hardcoded
    // No Storage — in-memory only, not shared across instances
}))

// BAD: Rate limiting can be disabled in production
if cfg.RateLimit.Enabled {
    app.Use(rateLimiter)
}
```

**Check Against Standards For:**
1. (CRITICAL) Rate limiting middleware exists and is registered on protected routes
2. (CRITICAL) Rate limiting cannot be disabled in production environment
3. (HIGH) Three-tier strategy implemented (Global, Export, Dispatch)
4. (HIGH) Redis-backed distributed storage (not in-memory only)
5. (HIGH) Key generation uses UserID > TenantID+IP > IP priority
6. (HIGH) Graceful degradation when Redis is unavailable
7. (MEDIUM) All rate limit values configurable via environment variables
8. (MEDIUM) 429 response includes `Retry-After` header
9. (MEDIUM) Sentinel errors used in Redis storage operations
10. (LOW) Rate limit key prefix isolates namespace (`ratelimit:`)

**Severity Ratings:**
- CRITICAL: No rate limiting middleware at all, rate limiting disabled in production
- HIGH: Single-tier only (no export/dispatch tiers), in-memory storage only (not distributed), no key generation strategy (IP only), no graceful degradation on Redis failure
- MEDIUM: Hardcoded rate limit values (not configurable), no Retry-After header, fmt.Errorf instead of sentinel errors
- LOW: Missing key prefix, rate limit logging not structured, no rate limit metrics/observability

**Output Format:**
```
## Rate Limiting Audit Findings

### Summary
- Rate limiting middleware: {Present / Absent}
- Tiers implemented: {Global, Export, Dispatch / Global only / None}
- Storage backend: {Redis / In-memory / None}
- Key generation: {UserID+TenantID+IP / IP only / Default}
- Production safety: {Force-enabled / Disableable / Not configured}
- Graceful degradation: {Yes / No}

### Critical Issues
[file:line] - Description

### High Issues
[file:line] - Description

### Medium Issues
[file:line] - Description

### Low Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 44: CORS Configuration Auditor

```prompt
Audit CORS (Cross-Origin Resource Sharing) configuration across the codebase for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: security.md § CORS Configuration (MANDATORY)}
---END STANDARDS---

**Search Patterns:**
- Go files: `**/*.go` — search for CORS middleware configuration, origin validation, preflight handling
- Config files: `**/*.env*`, `**/docker-compose*`, `**/config*.go` — search for CORS env vars
- Middleware files: `**/middleware/**`, `**/bootstrap/**` — search for CORS and Helmet middleware registration
- Keywords (Go): `cors`, `CORS`, `AllowOrigins`, `AllowMethods`, `AllowHeaders`, `fiber/middleware/cors`, `helmet`, `Helmet`, `HSTS`, `HSTSMaxAge`, `ContentSecurityPolicy`, `XFrameOptions`, `PermissionPolicy`
- Keywords (Config): `CORS_ALLOWED_ORIGINS`, `CORS_ALLOWED_METHODS`, `CORS_ALLOWED_HEADERS`, `TLS_TERMINATED_UPSTREAM`, `SERVER_TLS_CERT_FILE`

**CORS Patterns to Check:**

| Pattern | Risk Level | What to Look For |
|---------|:----------:|------------------|
| No CORS middleware at all | CRITICAL | No `cors.New()` or equivalent middleware registered |
| Wildcard origins in production | CRITICAL | `AllowOrigins: "*"` when `ENV_NAME=production` |
| Empty origins in production | CRITICAL | `CORS_ALLOWED_ORIGINS` not set in production |
| Hardcoded origins | HIGH | Origins in code instead of env var configuration |
| CORS after business logic | HIGH | CORS middleware placed after auth/handler — preflight fails |
| No production validation | HIGH | No check for wildcard/empty origins in production |
| Origin reflection without validation | CRITICAL | `AllowOriginsFunc` that returns true for all origins |
| No Helmet integration | MEDIUM | CORS configured but no Helmet security headers |
| HSTS not enabled with TLS | HIGH | TLS configured but `HSTSMaxAge` not set |

**Middleware Ordering Verification (MANDATORY — do not skip):**
Verify CORS is placed in the correct position in the middleware chain:
```
Recover → Request ID → CORS → Helmet (Security Headers) → Telemetry → Rate Limiter → Handler
```

**Production Validation Verification (MANDATORY — do not skip):**
1. **No wildcard origins**: Verify `*` is rejected when `ENV_NAME=production`
2. **No empty origins**: Verify empty `CORS_ALLOWED_ORIGINS` is rejected in production
3. **HTTPS origins**: Verify production origins use `https://` (not `http://`)
4. **Sentinel errors**: Verify validation uses sentinel errors (not `fmt.Errorf`)

**Helmet Integration Verification (MANDATORY — do not skip):**
1. **Security headers present**: Verify Helmet middleware is registered
2. **HSTS conditional**: Verify HSTS is enabled only when TLS is configured (cert file or TLSTerminatedUpstream)
3. **CSP configured**: Verify Content-Security-Policy header is set
4. **Cross-origin policies**: Verify CrossOriginEmbedderPolicy, CrossOriginOpenerPolicy, CrossOriginResourcePolicy

**Reference Implementation (GOOD — Go):**
```go
// GOOD: Configuration-driven CORS with production validation
app.Use(cors.New(cors.Config{
    AllowOrigins: cfg.Server.CORSAllowedOrigins,  // From env vars
    AllowMethods: cfg.Server.CORSAllowedMethods,
    AllowHeaders: cfg.Server.CORSAllowedHeaders,
}))

// GOOD: Production validation with sentinel errors
var (
    ErrCORSOriginsEmpty    = errors.New("CORS_ALLOWED_ORIGINS must be set in production")
    ErrCORSOriginsWildcard = errors.New("CORS_ALLOWED_ORIGINS must not contain wildcard (*) in production")
)

func validateProductionConfig(cfg *Config) error {
    if cfg.App.EnvName != "production" {
        return nil
    }
    origins := strings.TrimSpace(cfg.Server.CORSAllowedOrigins)
    if origins == "" {
        return ErrCORSOriginsEmpty
    }
    if strings.Contains(origins, "*") {
        return ErrCORSOriginsWildcard
    }
    return nil
}
```

**Reference Implementation (BAD — Go):**
```go
// BAD: Wildcard origins — allows any site to make requests
cors.Config{AllowOrigins: "*"}

// BAD: Hardcoded origins
cors.Config{AllowOrigins: "https://app.example.com"}

// BAD: No CORS middleware at all

// BAD: CORS after business logic — preflight fails
app.Use(authMiddleware)
app.Use(rateLimiter)
app.Use(cors.New(corsCfg))  // Too late

// BAD: Origin reflection without validation
cors.Config{
    AllowOriginsFunc: func(origin string) bool {
        return true  // Effectively same as wildcard
    },
}
```

**Check Against Standards For:**
1. (CRITICAL) CORS middleware is registered on the HTTP server
2. (CRITICAL) Wildcard origins (`*`) are not used in production
3. (CRITICAL) Empty origins are rejected in production
4. (CRITICAL) No origin reflection function that accepts all origins
5. (HIGH) Origins are configuration-driven via env vars (not hardcoded)
6. (HIGH) CORS is placed before Helmet and business logic in middleware chain
7. (HIGH) Production validation exists with sentinel errors
8. (HIGH) HSTS is enabled when TLS is configured
9. (MEDIUM) Helmet middleware is registered with security headers (CSP, X-Frame-Options, etc.)
10. (MEDIUM) Cross-origin policies are set (Embedder, Opener, Resource)
11. (LOW) Production origins use HTTPS (not HTTP)

**Severity Ratings:**
- CRITICAL: No CORS middleware, wildcard origins in production, empty origins in production, origin reflection accepting all
- HIGH: Hardcoded origins, CORS placed after business logic, no production validation, HSTS not enabled with TLS
- MEDIUM: No Helmet security headers, missing cross-origin policies, no CSP header
- LOW: HTTP origins in production, missing PermissionPolicy, verbose CORS error messages

**Output Format:**
```
## CORS Configuration Audit Findings

### Summary
- CORS middleware: {Present / Absent}
- Allowed origins source: {Env var / Hardcoded / Wildcard / Not configured}
- Production validation: {Present with sentinel errors / Present without sentinel errors / Absent}
- Middleware ordering: {Correct / Incorrect — position: {actual position}}
- Helmet integration: {Present / Absent}
- HSTS: {Enabled / Disabled / N/A (no TLS)}

### Critical Issues
[file:line] - Description

### High Issues
[file:line] - Description

### Medium Issues
[file:line] - Description

### Low Issues
[file:line] - Description

### Recommendations
1. ...
```
```

---

## Consolidated Report Template (Thorough)

<report-template-mandate>
MANDATORY: This template MUST be followed exactly as written. every section is REQUIRED — do not abbreviate, summarize, condense, or skip any section. The report MUST provide exhaustive detail for each dimension, with every issue fully documented including file location, code evidence, impact analysis, and remediation guidance. Omitting sections or reducing detail is FORBIDDEN regardless of the number of findings.
</report-template-mandate>

After all explorers complete, generate this report:

```markdown
# Production Readiness Audit Report

> **THOROUGH AUDIT** — This report provides exhaustive findings across all audited dimensions.
> every issue is documented with file location, evidence, impact analysis, and remediation guidance.

**Date:** {YYYY-MM-DDTHH:MM:SS}
**Codebase:** {project-name}
**Auditor:** Claude Code (Production Readiness Skill v3.0)
**Report Type:** Thorough

---

## Dashboard

| Overall Score | Classification | Critical | High | Medium | Low | HARD GATE Violations |
|:-------------:|:--------------:|:--------:|:----:|:------:|:---:|:--------------------:|
| **{score}/{dynamic_max} ({pct}%)** | **{classification}** | **{n}** | **{n}** | **{n}** | **{n}** | **{n}** |

### Readiness Classification

| Score Range | Classification | Deployment Recommendation |
|:-----------:|:--------------:|:-------------------------:|
| 90%+ | **Production Ready** | Clear to deploy |
| 75-89% | **Ready with Minor Remediation** | Deploy after addressing HIGH issues |
| 50-74% | **Needs Significant Work** | Do not deploy until CRITICAL/HIGH resolved |
| Below 50% | **Not Production Ready** | Major remediation required |

> **Current Status:** {classification} — {one-sentence summary of overall production readiness posture}

---

## Audit Configuration

| Property | Value |
|----------|-------|
| **Detected Stack** | {Go / TypeScript / Frontend / Mixed} |
| **Standards Loaded** | {list of loaded standards files} |
| **Active Dimensions** | {43 base + 1 conditional (max 44)} |
| **Max Possible Score** | {dynamic_max: 430 or 440} |
| **Conditional: Multi-Tenant** | {Active / Inactive} |

---

## Category Scoreboard

| Category | Score | % | Critical | High | Medium | Low | Status |
|:---------|------:|--:|:--------:|:----:|:------:|:---:|:------:|
| **A: Code Structure & Patterns** | {x}/110 | {pct}% | {n} | {n} | {n} | {n} | {PASS/NEEDS WORK/FAIL} |
| **B: Security & Access Control** | {x}/{90 or 100} | {pct}% | {n} | {n} | {n} | {n} | {PASS/NEEDS WORK/FAIL} |
| **C: Operational Readiness** | {x}/70 | {pct}% | {n} | {n} | {n} | {n} | {PASS/NEEDS WORK/FAIL} |
| **D: Quality & Maintainability** | {x}/100 | {pct}% | {n} | {n} | {n} | {n} | {PASS/NEEDS WORK/FAIL} |
| **E: Infrastructure & Hardening** | {x}/60 | {pct}% | {n} | {n} | {n} | {n} | {PASS/NEEDS WORK/FAIL} |
| **TOTAL** | **{x}/{dynamic_max}** | **{pct}%** | **{n}** | **{n}** | **{n}** | **{n}** | — |

Category status: PASS (>=70%), NEEDS WORK (40-69%), FAIL (<40%)

### Dimension Scores at a Glance

| # | Dimension | Score | Status | # | Dimension | Score | Status |
|---|-----------|:-----:|:------:|---|-----------|:-----:|:------:|
| 1 | Pagination Standards | {x}/10 | {icon} | 18 | Technical Debt | {x}/10 | {icon} |
| 2 | Error Framework | {x}/10 | {icon} | 19 | Testing Coverage | {x}/10 | {icon} |
| 3 | Route Organization | {x}/10 | {icon} | 20 | Dependency Mgmt | {x}/10 | {icon} |
| 4 | Bootstrap & Init | {x}/10 | {icon} | 21 | Performance | {x}/10 | {icon} |
| 5 | Runtime Safety | {x}/10 | {icon} | 22 | Concurrency | {x}/10 | {icon} |
| 6 | Auth Protection | {x}/10 | {icon} | 23 | Migrations | {x}/10 | {icon} |
| 7 | IDOR Protection | {x}/10 | {icon} | 24 | Container Security | {x}/10 | {icon} |
| 8 | SQL Safety | {x}/10 | {icon} | 25 | HTTP Hardening | {x}/10 | {icon} |
| 9 | Input Validation | {x}/10 | {icon} | 26 | CI/CD Pipeline | {x}/10 | {icon} |
| 11 | Telemetry | {x}/10 | {icon} | 28 | Core Dependencies | {x}/10 | {icon} |
| 12 | Health Checks | {x}/10 | {icon} | 29 | Naming Conventions | {x}/10 | {icon} |
| 13 | Configuration | {x}/10 | {icon} | 30 | Domain Modeling | {x}/10 | {icon} |
| 14 | Connections | {x}/10 | {icon} | 31 | Linting & Quality | {x}/10 | {icon} |
| 15 | Logging & PII | {x}/10 | {icon} | 32 | Makefile & Tooling | {x}/10 | {icon} |
| 16 | Idempotency | {x}/10 | {icon} | 33* | Multi-Tenant | {x}/10 | {icon} |
| 17 | API Documentation | {x}/10 | {icon} | 34 | License Headers | {x}/10 | {icon} |
| 35 | Nil/Null Safety | {x}/10 | {icon} | 36 | Resilience Patterns | {x}/10 | {icon} |
| 37 | Secret Scanning | {x}/10 | {icon} | 38 | API Versioning | {x}/10 | {icon} |
| 39 | Graceful Degradation | {x}/10 | {icon} | 40 | Caching Patterns | {x}/10 | {icon} |
| 41 | Data Encryption | {x}/10 | {icon} | 42 | Resource Leaks | {x}/10 | {icon} |
| 43 | Rate Limiting | {x}/10 | {icon} | 44 | CORS Configuration | {x}/10 | {icon} |

Status icons: PASS (>=7), WARN (4-6), FAIL (<4), N/A (conditional not active)
*33 = conditional dimension (Multi-Tenant) — included only if multi-tenant indicators detected*

---

## HARD GATE Violations

> HARD GATE violations are non-negotiable Ring standards failures that MUST be resolved before any deployment consideration. These represent structural non-compliance, not just quality gaps.

{If no violations: "No HARD GATE violations detected."}

{If violations exist:}

| # | Dimension | Violation | Location | Standards Reference |
|---|-----------|-----------|----------|---------------------|
| 1 | {dimension name} | {description of standards violation} | `{file:line}` | {standards-file.md} § {section} |

---

## Critical Blockers (Must Fix Before Production)

> These issues represent immediate risks to production safety, security, or data integrity. Deployment MUST NOT proceed until all CRITICAL issues are resolved.

{If no critical issues: "No critical blockers identified. All dimensions passed critical-level checks."}

{For each CRITICAL issue — MUST include all fields:}

### CB-{n}: {Short descriptive issue title}

| Property | Value |
|----------|-------|
| **Dimension** | #{num}. {Dimension Name} |
| **Category** | {A/B/C/D/E}: {Category Name} |
| **Severity** | CRITICAL |
| **Location** | `{file:line}` |
| **Standards Reference** | {standards-file.md} § {section name} |
| **HARD GATE Violation** | {Yes / No} |

**Description:**
{Detailed explanation of the issue — what is wrong and why it matters. Minimum 2-3 sentences.}

**Evidence:**
```{language}
// {file}:{line}
{relevant code snippet showing the problem — include enough context to understand the issue}
```

**Impact:**
{What could go wrong in production if this is not fixed. Be specific about failure modes, data risks, or security implications.}

**Recommended Fix:**
```{language}
// {file}:{line} — suggested change
{code showing the corrected approach aligned with Ring standards}
```

---

## High Priority Issues

> These issues represent significant risks or standards non-compliance. Address before production deployment or within the current sprint.

{If no high issues: "No high priority issues identified."}

{For each HIGH issue — MUST include all fields:}

### HP-{n}: {Short descriptive issue title}

| Property | Value |
|----------|-------|
| **Dimension** | #{num}. {Dimension Name} |
| **Category** | {A/B/C/D/E}: {Category Name} |
| **Severity** | HIGH |
| **Location** | `{file:line}` |
| **Standards Reference** | {standards-file.md} § {section name} |

**Description:**
{Detailed explanation of the issue. Minimum 2-3 sentences.}

**Evidence:**
```{language}
// {file}:{line}
{relevant code snippet showing the problem}
```

**Impact:**
{Production impact if not addressed.}

**Recommended Fix:**
```{language}
// {file}:{line} — suggested change
{code showing the corrected approach}
```

---

## Detailed Findings by Category

> This section provides exhaustive per-dimension findings. every dimension MUST include: a score breakdown, all issues organized by severity (CRITICAL first, then HIGH, MEDIUM, LOW), code evidence for each issue, and positive findings. Do not skip any dimension.

---

### Category A: Code Structure & Patterns ({x}/110)

---

#### Dimension 1: Pagination Standards

| Property | Value |
|----------|-------|
| **Score** | **{x}/10** |
| **Status** | {PASS (>=7) / WARN (4-6) / FAIL (<4)} |
| **Standards Source** | api-patterns.md § Pagination Patterns |
| **Issues Found** | {n} Critical, {n} High, {n} Medium, {n} Low |

**Summary:**
{2-3 sentence summary of the dimension's overall compliance. Describe what was checked, what the predominant pattern is, and the key gap (if any).}

{For each severity level that has issues, in order CRITICAL → HIGH → MEDIUM → LOW. Omit empty severity sections.}

##### CRITICAL Issues

| # | Location | Issue | HARD GATE | Standards Ref |
|---|----------|-------|:---------:|---------------|
| C1 | `{file:line}` | {brief description} | {Yes/No} | {section ref} |

**C1: {Issue title}**

- **Description:** {What is wrong and why it violates standards}
- **Evidence:**
  ```{language}
  // {file}:{line}
  {code showing the problem}
  ```
- **Impact:** {Production risk}
- **Recommended Fix:**
  ```{language}
  {corrected code}
  ```

##### HIGH Issues

| # | Location | Issue | Standards Ref |
|---|----------|-------|---------------|
| H1 | `{file:line}` | {brief description} | {section ref} |

**H1: {Issue title}**

- **Description:** {What is wrong}
- **Evidence:**
  ```{language}
  // {file}:{line}
  {code showing the problem}
  ```
- **Impact:** {Risk if not addressed}
- **Recommended Fix:**
  ```{language}
  {corrected code}
  ```

##### MEDIUM Issues

| # | Location | Issue | Standards Ref |
|---|----------|-------|---------------|
| M1 | `{file:line}` | {brief description} | {section ref} |

**M1: {Issue title}**
- **Description:** {What is wrong}
- **Evidence:** `{file}:{line}` — {brief code reference or description}
- **Recommended Fix:** {Brief guidance on how to align with standards}

##### LOW Issues

| # | Location | Issue |
|---|----------|-------|
| L1 | `{file:line}` | {brief description} |

- **L1:** {One-line description with fix guidance}

##### What Was Done Well

{List positive findings. If the dimension is fully compliant, describe what was correctly implemented. Minimum 1 item.}

- {Positive finding 1 — cite specific file or pattern}
- {Positive finding 2}

---

#### Dimension 2: Error Framework

{SAME structure as Dimension 1 — property table, summary, severity-grouped issues, positive findings}

---

#### Dimension 3: Route Organization

{SAME structure}

---

#### Dimension 4: Bootstrap & Initialization

{SAME structure}

---

#### Dimension 5: Runtime Safety

{SAME structure}

---

#### Dimension 28: Core Dependencies & Frameworks

{SAME structure}

---

#### Dimension 29: Naming Conventions

{SAME structure}

---

#### Dimension 30: Domain Modeling

{SAME structure}

---

#### Dimension 35: Nil/Null Safety

{SAME structure as Dimension 1}

---

#### Dimension 38: API Versioning

{SAME structure as Dimension 1}

---

#### Dimension 42: Resource Leak Prevention

{SAME structure as Dimension 1}

---

### Category B: Security & Access Control ({x}/{90 or 100})

---

#### Dimension 6: Auth Protection

{SAME structure as Dimension 1}

---

#### Dimension 7: IDOR & Access Control

{SAME structure}

---

#### Dimension 8: SQL Safety

{SAME structure}

---

#### Dimension 9: Input Validation

{SAME structure}

---

#### Dimension 37: Secret Scanning

{SAME structure as Dimension 1}

---

#### Dimension 41: Data Encryption at Rest

{SAME structure as Dimension 1}

---

#### Dimension 43: Rate Limiting

{SAME structure as Dimension 1}

---

#### Dimension 44: CORS Configuration

{SAME structure as Dimension 1}

---

#### Dimension 33: Multi-Tenant Patterns *(CONDITIONAL)*

{If MULTI_TENANT=false: "**Dimension not activated** — No multi-tenant indicators detected in this codebase. Score excluded from total."}

{If MULTI_TENANT=true: SAME structure as Dimension 1}

---

### Category C: Operational Readiness ({x}/70)

---

#### Dimension 11: Telemetry & Observability

{SAME structure as Dimension 1}

---

#### Dimension 12: Health Checks

{SAME structure}

---

#### Dimension 13: Configuration Management

{SAME structure}

---

#### Dimension 14: Connection Management

{SAME structure}

---

#### Dimension 15: Logging & PII Safety

{SAME structure}

---

#### Dimension 36: Resilience Patterns

{SAME structure as Dimension 1}

---

#### Dimension 39: Graceful Degradation

{SAME structure as Dimension 1}

---

### Category D: Quality & Maintainability ({x}/100)

---

#### Dimension 16: Idempotency

{SAME structure as Dimension 1}

---

#### Dimension 17: API Documentation

{SAME structure}

---

#### Dimension 18: Technical Debt

{SAME structure}

---

#### Dimension 19: Testing Coverage

{SAME structure}

---

#### Dimension 20: Dependency Management

{SAME structure}

---

#### Dimension 21: Performance Patterns

{SAME structure}

---

#### Dimension 22: Concurrency Safety

{SAME structure}

---

#### Dimension 23: Migration Safety

{SAME structure}

---

#### Dimension 31: Linting & Code Quality

{SAME structure}

---

#### Dimension 40: Caching Patterns

{SAME structure as Dimension 1}

---

### Category E: Infrastructure & Hardening ({x}/60)

---

#### Dimension 24: Container Security

{SAME structure as Dimension 1}

---

#### Dimension 25: HTTP Hardening

{SAME structure}

---

#### Dimension 26: CI/CD Pipeline

{SAME structure}

---

#### Dimension 27: Async Reliability

{SAME structure}

---

#### Dimension 32: Makefile & Dev Tooling

{SAME structure}

---

#### Dimension 34: License Headers

{SAME structure as Dimension 1 — if no LICENSE file exists, all items reported as N/A with evidence}

---

## Standards Compliance Cross-Reference

| # | Dimension | Standards Source | Section | Status | Score |
|---|-----------|----------------|---------|:------:|------:|
| 1 | Pagination Standards | api-patterns.md | Pagination Patterns | {PASS/FAIL} | {x}/10 |
| 2 | Error Framework | domain.md | Error Codes, Error Handling | {PASS/FAIL} | {x}/10 |
| 3 | Route Organization | architecture.md | Architecture Patterns, Directory Structure | {PASS/FAIL} | {x}/10 |
| 4 | Bootstrap & Initialization | bootstrap.md | Bootstrap | {PASS/FAIL} | {x}/10 |
| 5 | Runtime Safety | (generic) | — | {PASS/FAIL} | {x}/10 |
| 6 | Auth Protection | security.md | Access Manager Integration | {PASS/FAIL} | {x}/10 |
| 7 | IDOR & Access Control | (generic) | — | {PASS/FAIL} | {x}/10 |
| 8 | SQL Safety | (generic) | — | {PASS/FAIL} | {x}/10 |
| 9 | Input Validation | core.md | Frameworks & Libraries | {PASS/FAIL} | {x}/10 |
| 11 | Telemetry & Observability | bootstrap.md + sre.md | Observability, OpenTelemetry | {PASS/FAIL} | {x}/10 |
| 12 | Health Checks | sre.md | Health Checks | {PASS/FAIL} | {x}/10 |
| 13 | Configuration Management | core.md | Configuration | {PASS/FAIL} | {x}/10 |
| 14 | Connection Management | core.md | Core Dependency: lib-commons | {PASS/FAIL} | {x}/10 |
| 15 | Logging & PII Safety | quality.md | Logging | {PASS/FAIL} | {x}/10 |
| 16 | Idempotency | idempotency.md | Full module | {PASS/FAIL} | {x}/10 |
| 17 | API Documentation | api-patterns.md | OpenAPI (Swaggo) | {PASS/FAIL} | {x}/10 |
| 18 | Technical Debt | (generic) | — | {PASS/FAIL} | {x}/10 |
| 19 | Testing Coverage | quality.md | Testing | {PASS/FAIL} | {x}/10 |
| 20 | Dependency Management | core.md | Frameworks & Libraries | {PASS/FAIL} | {x}/10 |
| 21 | Performance Patterns | (generic) | — | {PASS/FAIL} | {x}/10 |
| 22 | Concurrency Safety | architecture.md | Concurrency Patterns | {PASS/FAIL} | {x}/10 |
| 23 | Migration Safety | core.md | Database patterns | {PASS/FAIL} | {x}/10 |
| 24 | Container Security | devops.md | Containers | {PASS/FAIL} | {x}/10 |
| 25 | HTTP Hardening | (generic) | — | {PASS/FAIL} | {x}/10 |
| 26 | CI/CD Pipeline | devops.md | CI section | {PASS/FAIL} | {x}/10 |
| 27 | Async Reliability | messaging.md | RabbitMQ Worker Pattern | {PASS/FAIL} | {x}/10 |
| 28 | Core Dependencies | core.md | lib-commons, Frameworks | {PASS/FAIL} | {x}/10 |
| 29 | Naming Conventions | core.md + api-patterns.md | Naming conventions | {PASS/FAIL} | {x}/10 |
| 30 | Domain Modeling | domain.md + domain-modeling.md | ToEntity, Always-Valid | {PASS/FAIL} | {x}/10 |
| 31 | Linting & Code Quality | quality.md | Linting | {PASS/FAIL} | {x}/10 |
| 32 | Makefile & Dev Tooling | devops.md | Makefile Standards | {PASS/FAIL} | {x}/10 |
| 35 | Nil/Null Safety | (nil-safety-reviewer) | Nil Patterns | {PASS/FAIL} | {x}/10 |
| 36 | Resilience Patterns | (generic) | Resilience Patterns | {PASS/FAIL} | {x}/10 |
| 37 | Secret Scanning | (generic) | Secret Detection | {PASS/FAIL} | {x}/10 |
| 38 | API Versioning | api-patterns.md | API Versioning | {PASS/FAIL} | {x}/10 |
| 39 | Graceful Degradation | (generic) | Degradation Patterns | {PASS/FAIL} | {x}/10 |
| 40 | Caching Patterns | (generic) | Cache Management | {PASS/FAIL} | {x}/10 |
| 41 | Data Encryption | security.md | Encryption at Rest | {PASS/FAIL} | {x}/10 |
| 42 | Resource Leaks | (generic) | Resource Lifecycle | {PASS/FAIL} | {x}/10 |
| 43 | Rate Limiting | security.md | Rate Limiting | {PASS/FAIL} | {x}/10 |
| 44 | CORS Configuration | security.md | CORS Configuration | {PASS/FAIL} | {x}/10 |
| 33 | Multi-Tenant Patterns | multi-tenant.md | Full module | {PASS/FAIL/N/A} | {x}/10 |
| 34 | License Headers | core.md | License section | {PASS/FAIL/N/A} | {x}/10 |

*Dimension 33 is conditional — excluded from scoring when MULTI_TENANT=false*

---

## Issue Index by Severity

> Complete cross-cutting index of all issues found across all dimensions, grouped by severity. Use this for quick reference and remediation tracking.

### All CRITICAL Issues ({total_count})

| # | ID | Dimension | Category | Location | Issue | HARD GATE |
|---|----|-----------|----------|----------|-------|:---------:|
| 1 | CB-1 | {dimension} | {cat} | `{file:line}` | {description} | {Yes/No} |

### All HIGH Issues ({total_count})

| # | ID | Dimension | Category | Location | Issue |
|---|----|-----------|----------|----------|-------|
| 1 | HP-1 | {dimension} | {cat} | `{file:line}` | {description} |

### All MEDIUM Issues ({total_count})

| # | Dimension | Category | Location | Issue |
|---|-----------|----------|----------|-------|
| 1 | {dimension} | {cat} | `{file:line}` | {description} |

### All LOW Issues ({total_count})

| # | Dimension | Category | Location | Issue |
|---|-----------|----------|----------|-------|
| 1 | {dimension} | {cat} | `{file:line}` | {description} |

---

## Remediation Roadmap

> Prioritized action plan organized by urgency. Each phase includes estimated effort to help with sprint planning.

### Phase 1: Immediate (before any deployment)

> Blocking issues that MUST be resolved before production. These are CRITICAL severity items and HARD GATE violations.

| Priority | ID | Dimension | Issue | Estimated Effort |
|:--------:|----|-----------|-------|:----------------:|
| 1 | CB-{n} | {dimension} | {short description} | {hours}h |

**Phase 1 Total Estimated Effort:** {X} hours

### Phase 2: Short-term (within 1 sprint)

> HIGH severity items to address in the current or next sprint before considering the system production-stable.

| Priority | ID | Dimension | Issue | Estimated Effort |
|:--------:|----|-----------|-------|:----------------:|
| 1 | HP-{n} | {dimension} | {short description} | {hours}h |

**Phase 2 Total Estimated Effort:** {X} hours

### Phase 3: Medium-term (within 1 quarter)

> MEDIUM severity improvements to plan for upcoming sprints. These improve compliance and reduce technical debt.

| Priority | Dimension | Issue | Estimated Effort |
|:--------:|-----------|-------|:----------------:|
| 1 | {dimension} | {short description} | {hours}h |

**Phase 3 Total Estimated Effort:** {X} hours

### Phase 4: Backlog (track but do not block deployment)

> LOW severity enhancements. Create tickets in issue tracker for future consideration.

| Dimension | Issue |
|-----------|-------|
| {dimension} | {short description} |

---

## Appendix A: Files Audited

| # | File Path | Lines | Dimensions That Examined It |
|---|-----------|------:|:---------------------------|
| 1 | `{file path}` | {n} | {comma-separated dimension numbers} |

**Total:** {n} files, {n} lines of code audited

---

## Appendix B: Audit Metadata

| Property | Value |
|----------|-------|
| **Audit Date** | {YYYY-MM-DD HH:MM} |
| **Audit Duration** | {X} minutes |
| **Explorers Launched** | {43 or 44} |
| **Files Examined** | {X} |
| **Lines of Code** | {X} |
| **Skill Version** | 3.0 |
| **Report Type** | Thorough |
| **Standards Source** | Ring Development Standards (GitHub) |
| **Standards Files Loaded** | {list} |
| **Stack Detected** | {Go / TypeScript / Frontend / Mixed} |
| **Dimensions** | {43 + conditional count} |

---

## CONDITIONAL DIMENSION (Multi-Tenant)

### Agent 33: Multi-Tenant Patterns Auditor *(CONDITIONAL)*

```prompt
CONDITIONAL: Only run this agent if MULTI_TENANT=true was detected during stack detection. If the project does not use multi-tenancy (no tenant config, no pool manager, no tenant middleware), SKIP this agent entirely and report: "Dimension 33 skipped — single-tenant project (no multi-tenant indicators detected)."

If multi-tenant IS detected, audit multi-tenant architecture patterns for production readiness against the COMPLETE canonical model defined in multi-tenant.md.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: Full multi-tenant.md standard}
---END STANDARDS---

**Search Patterns:**
- Files: `**/tenant*.go`, `**/pool*.go`, `**/middleware*.go`, `**/context*.go`
- Keywords: `tenantID`, `TenantManager`, `TenantContext`, `schema`, `search_path`
- Also search: `**/jwt*.go`, `**/auth*.go` for tenant extraction
- Config files: `**/config.go`, `**/bootstrap/*.go` for env var declarations
- Routes: `**/routes.go`, `**/router*.go` for middleware ordering
- Redis: `**/redis*.go`, `**/*redis*` for key prefixing (including Lua scripts)
- S3/Storage: `**/storage*.go`, `**/s3*.go` for object key prefixing
- RabbitMQ: `**/rabbitmq*.go`, `**/producer*.go`, `**/consumer*.go` for isolation layers
- Tests: `**/*_test.go` for backward compatibility test
- Non-canonical: source implementation files that define custom tenant resolvers/middleware/pool managers outside canonical lib-commons integration paths (exclude docs, tests, fixtures, vendored code)
- go.mod: lib-commons version, lib-auth version
- M2M: `**/m2m*.go`, `**/credential*.go`, `**/secret*.go` for M2M credential handling

**Reference Implementation (GOOD):**
```go
// Canonical env vars in config.go (15 MANDATORY — APPLICATION_NAME + 14 MULTI_TENANT_*)
ApplicationName                        string `env:"APPLICATION_NAME"`
MultiTenantEnabled                     bool   `env:"MULTI_TENANT_ENABLED" default:"false"`
MultiTenantURL                         string `env:"MULTI_TENANT_URL"`
MultiTenantRedisHost                   string `env:"MULTI_TENANT_REDIS_HOST"`
MultiTenantRedisPort                   string `env:"MULTI_TENANT_REDIS_PORT" default:"6379"`
MultiTenantRedisPassword               string `env:"MULTI_TENANT_REDIS_PASSWORD"`
MultiTenantRedisTLS                    bool   `env:"MULTI_TENANT_REDIS_TLS"`
MultiTenantMaxTenantPools              int    `env:"MULTI_TENANT_MAX_TENANT_POOLS" default:"100"`
MultiTenantIdleTimeoutSec              int    `env:"MULTI_TENANT_IDLE_TIMEOUT_SEC" default:"300"`
MultiTenantTimeout                     int    `env:"MULTI_TENANT_TIMEOUT" default:"30"`
MultiTenantCircuitBreakerThreshold     int    `env:"MULTI_TENANT_CIRCUIT_BREAKER_THRESHOLD" default:"5"`
MultiTenantCircuitBreakerTimeoutSec    int    `env:"MULTI_TENANT_CIRCUIT_BREAKER_TIMEOUT_SEC" default:"30"`
MultiTenantServiceAPIKey               string `env:"MULTI_TENANT_SERVICE_API_KEY"`
MultiTenantCacheTTLSec                 int    `env:"MULTI_TENANT_CACHE_TTL_SEC" default:"120"`
MultiTenantConnectionsCheckIntervalSec int    `env:"MULTI_TENANT_CONNECTIONS_CHECK_INTERVAL_SEC" default:"30"`

// TenantMiddleware with multi-module WithPG/WithMB options from lib-commons v5
import tmmiddleware "github.com/LerianStudio/lib-commons/v5/commons/dispatch layer/middleware"

ttMiddleware := tmmiddleware.NewTenantMiddleware(
    tmmiddleware.WithPG(pgOnboardingManager, constant.ModuleOnboarding),
    tmmiddleware.WithPG(pgTransactionManager, constant.ModuleTransaction),
    tmmiddleware.WithMB(mbOnboardingManager, constant.ModuleOnboarding),
    tmmiddleware.WithMB(mbTransactionManager, constant.ModuleTransaction),
    tmmiddleware.WithTenantCache(tenantCache),
    tmmiddleware.WithTenantLoader(tenantClient),
)

// Per-route auth-before-tenant ordering (MANDATORY)
// Auth validates JWT BEFORE tenant middleware calls Tenant Manager API
f.Get("/v1/organizations/:id", auth.Authorize(...), WhenEnabled(ttHandler), handler)

// Circuit breaker on Tenant Manager client (MANDATORY)
clientOpts = append(clientOpts,
    client.WithCircuitBreaker(cfg.MultiTenantCircuitBreakerThreshold, timeout),
    client.WithServiceAPIKey(cfg.MultiTenantServiceAPIKey),
)

// Module-specific connection from context
db := tmcore.GetPGContext(ctx, constant.ModuleOnboarding)
// Single-module alternative:
db := tmcore.GetPGContext(ctx)
// MongoDB:
mongoDB := tmcore.GetMBContext(ctx, constant.ModuleOnboarding)

// Redis key prefixing — ALL operations including Lua scripts
key := valkey.GetKeyContext(ctx, "cache-key")
// Lua scripts: prefix ALL KEYS[] and ARGV[] before execution
prefixedKey := valkey.GetKeyContext(ctx, transactionKey)
result, err := script.Run(ctx, rds, []string{prefixedKey}, finalArgs...).Result()

// S3 key prefixing — ALL object operations
key := s3.GetS3KeyStorageContext(ctx, originalKey)

// RabbitMQ: Layer 1 (vhost isolation) + Layer 2 (X-Tenant-ID header)
ch, err := tmrabbitmq.Manager.GetChannel(ctx, tenantID) // Layer 1: vhost
headers["X-Tenant-ID"] = tenantID                        // Layer 2: audit header

// Repository using tenant-routed database connection
func (r *Repo) Find(ctx context.Context, id uuid.UUID) (*Entity, error) {
    db := tmcore.GetPGContext(ctx, constant.ModuleTransaction)
    if db == nil {
        return nil, fmt.Errorf("tenant postgres connection missing from context for module %s", constant.ModuleTransaction)
    }
    find := squirrel.Select(columnList...).
        From(r.tableName).
        Where(squirrel.Expr("id = ?", id)).
        PlaceholderFormat(squirrel.Dollar)
    // ...
}

// Error handling with sentinel errors
case errors.Is(err, core.ErrTenantNotFound):     // → 404
case errors.Is(err, core.ErrManagerClosed):       // → 503
case errors.Is(err, core.ErrServiceNotConfigured): // → 503
case core.IsTenantNotProvisionedError(err):       // → 422
case errors.Is(err, core.ErrCircuitBreakerOpen):  // → 503

// Backward compatibility test (MANDATORY)
func TestMultiTenant_BackwardCompatibility(t *testing.T) {
    if h.IsMultiTenantEnabled() {
        t.Skip("Skipping backward compatibility test - multi-tenant mode is enabled")
    }
    // Create resources WITHOUT tenant context — MUST work in single-tenant mode
}

// Mandatory metrics (no-op in single-tenant mode)
// tenant_connections_total, tenant_connection_errors_total,
// tenant_consumers_active, tenant_messages_processed_total

// M2M credentials (ONLY if service has targetServices)
// L1 (sync.Map, 30s) → L2 (Redis, 300s) → AWS Secrets Manager
// Cache-bust on 401: delete L2 → delete L1 → re-fetch
m2mProvider = m2m.NewM2MCredentialProvider(redisConn, awsClient, logger, metrics)
```

**Reference Implementation (BAD):**
```go
// BAD: Non-canonical env var names
TenantManagerURL string `env:"TENANT_MANAGER_URL"`     // WRONG: must be MULTI_TENANT_URL
TenantEnabled    bool   `env:"TENANT_ENABLED"`          // WRONG: must be MULTI_TENANT_ENABLED

// BAD: Query using static connection instead of tenant-routed context
func (r *Repo) FindByID(ctx context.Context, id uuid.UUID) (*Entity, error) {
    return r.db.QueryRowContext(ctx, "SELECT * FROM entities WHERE id = $1", id)
    // WRONG: must use tmcore.GetPGContext(ctx, module) for tenant database routing
}

// BAD: Tenant ID from request header (can be spoofed)
func GetTenantID(c *fiber.Ctx) string {
    return c.Get("X-Tenant-ID")  // User-controlled!
}

// BAD: Global middleware (bypasses auth-first ordering)
app.Use(tenantMiddleware)  // WRONG: must use per-route WhenEnabled composition

// BAD: Using GetPGContext without module in multi-module service
db := tmcore.GetPGContext(ctx)  // WRONG: use GetPGContext(ctx, module) for multi-module services

// BAD: Missing circuit breaker on Tenant Manager client
tmClient := client.New(cfg.MultiTenantURL)  // WRONG: must use WithCircuitBreaker + WithServiceAPIKey

// BAD: Unprefixed Redis key in multi-tenant mode
rds.Set(ctx, "cache-key", value, ttl)  // WRONG: must use valkey.GetKeyContext(ctx, "cache-key")

// BAD: Unprefixed S3 key in multi-tenant mode
s3Client.PutObject(ctx, "bucket", "object-key", body)  // WRONG: must use s3.GetS3KeyStorageContext

// BAD: Non-canonical custom files (MUST be removed from source paths)
// internal/tenant/resolver.go          ← FORBIDDEN
// internal/middleware/tenant_middleware.go ← FORBIDDEN
// pkg/multitenancy/pool.go             ← FORBIDDEN

// BAD: lib-commons v2/v3/v4 imports
import tenantmanager "github.com/LerianStudio/lib-commons/v2/..."  // WRONG: must be v5

// BAD: RabbitMQ with only X-Tenant-ID header (no vhost isolation)
headers["X-Tenant-ID"] = tenantID  // Audit only, NOT isolation — must also use tmrabbitmq.Manager

// BAD: Using deprecated functions — NON-COMPLIANT, MUST migrate to current API
// WithPostgresManager, WithMongoManager, WithModule, GetMongoFromContext,
// GetKeyFromContext, GetPGConnectionFromContext, GetPGConnectionContext,
// GetMongoContext, ResolvePostgres, ResolveMongo, ResolveModuleDB,
// SetTenantIDInContext, GetPostgresForTenant, GetMongoForTenant,
// ContextWithPGConnection, ContextWithMongo, ContextWithModulePGConnection,
// GetModulePostgresForTenant, MultiPoolMiddleware, DualPoolMiddleware,
// SettingsWatcher, NewSettingsWatcher
```

**Check Against Ring Standards For:**

HARD GATES (Score = 0 if any fails):
1. (HARD GATE) Tenant ID extracted from JWT claims (not user-controlled headers/params) per multi-tenant.md
2. (HARD GATE) All database queries use tenant-routed connections via tmcore.GetPGContext/tmcore.GetMBContext (not static connections or package-level singletons)
3. (HARD GATE) TenantMiddleware with WithPG/WithMB from lib-commons v5 injects tenant into request context with module-specific connections
4. (HARD GATE) lib-commons v5 (not v2/v3/v4) for all dispatch layer sub-package imports — deprecated functions (WithPostgresManager, MultiPoolMiddleware, DualPoolMiddleware, ResolvePostgres, ResolveModuleDB, etc.) are NON-COMPLIANT

WARNINGS (does not zero the score, but flagged as HIGH):
5. (WARNING) Non-canonical source implementation files detected: custom tenant resolvers, manual pool managers, or wrapper middleware in source paths (internal/, pkg/, cmd/) outside canonical lib-commons integration paths. Excludes docs, tests, fixtures, vendored code.

Canonical Environment Variables:
6. APPLICATION_NAME always required (used for Tenant Manager settings resolution regardless of mode). When MULTI_TENANT_ENABLED=true, all 14 MULTI_TENANT_* env vars must also be declared in the config struct with exact names: MULTI_TENANT_ENABLED, MULTI_TENANT_URL, MULTI_TENANT_REDIS_HOST, MULTI_TENANT_REDIS_PORT, MULTI_TENANT_REDIS_PASSWORD, MULTI_TENANT_REDIS_TLS, MULTI_TENANT_MAX_TENANT_POOLS, MULTI_TENANT_IDLE_TIMEOUT_SEC, MULTI_TENANT_TIMEOUT, MULTI_TENANT_CIRCUIT_BREAKER_THRESHOLD, MULTI_TENANT_CIRCUIT_BREAKER_TIMEOUT_SEC, MULTI_TENANT_SERVICE_API_KEY, MULTI_TENANT_CACHE_TTL_SEC, MULTI_TENANT_CONNECTIONS_CHECK_INTERVAL_SEC. Single-tenant mode (MULTI_TENANT_ENABLED=false or absent) must work without any MULTI_TENANT_* vars set.
7. No non-canonical env var names for tenant configuration (e.g., TENANT_MANAGER_URL, TENANT_ENABLED, MULTI_TENANT_ENVIRONMENT are violations — APPLICATION_NAME is valid)

Middleware & Routing:
8. Auth-before-tenant ordering: auth.Authorize() MUST run before WhenEnabled(ttHandler) on every route (SECURITY CRITICAL)
9. Per-route composition via WhenEnabled helper (not global app.Use(tenantMiddleware))
10. TenantMiddleware with WithPG/WithMB options for module-specific connection injection
11. Tenant middleware passed as nil when MULTI_TENANT_ENABLED=false (WhenEnabled handles nil → c.Next())

Connection Management:
12. TenantConnectionManager (PostgresManager/MongoManager) for database-per-tenant isolation
13. Correct resolution function: tmcore.GetPGContext(ctx) (single-module) or tmcore.GetPGContext(ctx, module) (multi-module) or tmcore.GetMBContext(ctx, module) (MongoDB)
14. Cross-module connection injection (both modules in context for multi-module services)
15. WithConnectionsCheckInterval on pgManager for async settings revalidation (PostgreSQL only)

Client Configuration:
16. Circuit breaker configured on Tenant Manager HTTP client (client.WithCircuitBreaker)
17. Service API key authentication configured (client.WithServiceAPIKey)

Data Isolation:
18. Tenant-scoped Redis cache keys via valkey.GetKeyContext for ALL operations (including Lua script KEYS[] and ARGV[])
19. Tenant-scoped S3 object keys via s3.GetS3KeyStorageContext for ALL operations
20. No cross-tenant data leakage in list/search operations

RabbitMQ (if detected):
21. Layer 1: vhost isolation via tmrabbitmq.Manager.GetChannel
22. Layer 2: X-Tenant-ID header injection on all messages (both layers MANDATORY)
23. Multi-tenant consumer via tmconsumer.MultiTenantConsumer (on-demand initialization)

Error Handling:
24. Sentinel error mapping: ErrTenantNotFound→404, *TenantSuspendedError→403, ErrManagerClosed→503, ErrServiceNotConfigured→503, IsTenantNotProvisionedError→422, ErrCircuitBreakerOpen→503
25. ErrTenantContextRequired in repositories when tenant context is missing

Backward Compatibility:
26. Service works with MULTI_TENANT_ENABLED=false (default) — no MULTI_TENANT_* vars required
27. TestMultiTenant_BackwardCompatibility test exists and validates single-tenant mode
28. Service starts without Tenant Manager running

Metrics:
29. All 4 core metrics present: tenant_connections_total, tenant_connection_errors_total, tenant_consumers_active, tenant_messages_processed_total
30. Metrics are no-op in single-tenant mode (zero overhead)

Graceful Shutdown:
31. Connection managers closed during shutdown (manager.Close() in shutdown hooks)

Event-Driven Discovery:
32. EventListener configured (Redis Pub/Sub subscription for tenant lifecycle events)
33. NewTenantPubSubRedisClient used for Redis client (not manual libRedis.Config)
34. NewTenantEventListener wired with PubSub Redis client
35. TenantCache + TenantLoader wired to TenantMiddleware
36. TenantLoader.SetOnTenantLoaded callback configured (starts consumer after lazy-load)
37. OnTenantAdded callback: invalidates cache + starts consumer for new tenant
38. OnTenantRemoved callback: stops consumer + closes connections + invalidates cache
39. StopConsumer called before CloseConnection on tenant removal (ordering matters)

M2M Credentials (CONDITIONAL — activation criteria below):
Activation rule: M2M checks apply ONLY when BOTH conditions are met:
  (a) Service declares a non-empty `targetServices` in typed config/DTO/module wiring, AND
  (b) Outbound service-to-service credential provider usage is detected in code paths (e.g., secretsmanager.GetM2MCredentials, m2m.NewM2MCredentialProvider).
If either condition is missing, mark M2M section as N/A and do not deduct score.
40. M2M credential provider with two-level cache: L1 (sync.Map, 30s) → L2 (Redis) → AWS Secrets Manager
41. Cache-bust on 401: invalidate L2 → L1 → re-fetch
42. 6 M2M metrics: m2m_credential_l1_cache_hits, m2m_credential_l2_cache_hits, m2m_credential_cache_misses, m2m_credential_fetch_errors, m2m_credential_fetch_duration_seconds, m2m_credential_invalidations
43. Credentials MUST NOT be logged or stored in environment variables
44. Redis key for credentials uses valkey.GetKeyContext with pattern: tenant:{tenantOrgID}:m2m:{targetService}:credentials

**Severity Ratings:**
- CRITICAL: Queries using static connections instead of tenant-routed tmcore.GetPGContext/GetMBContext (HARD GATE violation)
- CRITICAL: Tenant ID from user-controlled input (HARD GATE violation)
- CRITICAL: Missing TenantMiddleware with WithPG/WithMB from lib-commons v5 (HARD GATE violation)
- CRITICAL: Using deprecated functions (WithPostgresManager, MultiPoolMiddleware, DualPoolMiddleware, ResolvePostgres, ResolveModuleDB, etc.) — NON-COMPLIANT, MUST migrate to current API
- CRITICAL: lib-commons v2/v3/v4 imports instead of v5 (HARD GATE violation)
- CRITICAL: Auth-after-tenant ordering — JWT not validated before Tenant Manager API call (security vulnerability)
- CRITICAL: Global app.Use(tenantMiddleware) instead of per-route WhenEnabled composition (bypasses auth ordering)
- HIGH: Non-canonical env var names (e.g., TENANT_MANAGER_URL instead of MULTI_TENANT_URL)
- HIGH: Non-canonical source files detected — custom tenant resolvers/middleware/pool managers in source paths
- HIGH: Missing circuit breaker on Tenant Manager client (cascading failure risk across all tenants)
- HIGH: Missing service API key authentication (Tenant Manager calls unauthenticated)
- HIGH: No TenantConnectionManager for connection management
- HIGH: Cache keys not tenant-scoped (Redis or S3)
- HIGH: Missing cross-module connection injection
- HIGH: Missing backward compatibility test (TestMultiTenant_BackwardCompatibility)
- HIGH: RabbitMQ missing vhost isolation (Layer 2 header alone is NOT compliant)
- HIGH: M2M credentials logged or stored in env vars (if targetServices detected)
- MEDIUM: Inconsistent tenant extraction across modules
- MEDIUM: Missing sentinel error handling (ErrManagerClosed, ErrCircuitBreakerOpen, *TenantSuspendedError, etc.)
- MEDIUM: Missing graceful shutdown of connection managers
- MEDIUM: Metrics not present or not no-op in single-tenant mode
- MEDIUM: Redis Lua script keys not prefixed with valkey.GetKeyContext
- LOW: Missing tenant validation in non-critical paths

**Output Format:**
```
## Multi-Tenant Patterns Audit Findings

### Summary
- Multi-tenant detection: Yes/No/N/A
- lib-commons version: v5 / v4 / v3 / v2 / Missing
- Tenant extraction: JWT / Header / Missing
- TenantMiddleware (WithPG/WithMB): Yes / No / Custom / Missing
- Auth-before-tenant ordering: Yes / No / Inconsistent
- Route composition: Per-route WhenEnabled / Global app.Use / Mixed
- APPLICATION_NAME: Present / Missing
- Canonical MULTI_TENANT_* env vars (when MT enabled): X/14 present with correct names
- Non-canonical env vars detected: [list or "None"]
- Non-canonical source files detected: [list or "None"]
- Circuit breaker on TM client: Yes / No
- Service API key configured: Yes / No
- Connection resolution: tmcore.GetPGContext(ctx, module) / tmcore.GetPGContext(ctx) / tmcore.GetMBContext / Custom / Missing
- Redis key prefixing: Yes / Partial / No (Lua scripts: Yes/No)
- S3 key prefixing: Yes / No / N/A
- RabbitMQ isolation: Both layers / Header only / Missing / N/A
- Event-driven discovery: NewTenantPubSubRedisClient + NewTenantEventListener + TenantCache + TenantLoader + SetOnTenantLoaded / Partial / Missing
- Backward compatibility test: Yes / No
- Backward compatibility mode: Works without MT vars / Requires MT vars
- Mandatory metrics: X/4 present (no-op in ST: Yes/No)
- Graceful shutdown: Manager.Close() called / Missing
- M2M credentials: Compliant / Non-compliant / N/A (no targetServices detected)

### HARD GATE Violations
[file:line] - Description (HARD GATE: Score = 0)

### Critical Issues
[file:line] - Description

### High Issues
[file:line] - Description

### Medium Issues
[file:line] - Description

### Recommendations
1. ...
```
```

