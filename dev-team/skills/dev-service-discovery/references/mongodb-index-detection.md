# MongoDB Index Detection & Script Generation

**Only execute this phase if MongoDB was detected in any module during Phase 3.**

This phase detects MongoDB index definitions in two places:
1. **In-code indexes** — `EnsureIndexes()` methods in repository files that create indexes at startup
2. **Script-based indexes** — `scripts/mongodb/*.js` files meant to be run via `mongosh`

---

## Step 1: Detect In-Code Index Definitions

```text
For EACH module where MongoDB was detected:

1. Find EnsureIndexes methods:
   - Grep tool (regex): grep -E 'func.*EnsureIndexes|IndexModel|CreateIndex|createIndex'
     in {base_path}mongodb/ OR {base_path}mongo/ --include="*.go"
   - For each file with matches, extract:
     a. Collection name (from the receiver's collection field or constant)
     b. Index keys (from bson.D{{Key: "field", Value: 1}})
     c. Index options (unique, sparse, TTL, etc.)
     d. Index name (if specified via SetName)

2. Parse index models:
   - Look for mongo.IndexModel{} structs
   - Extract Keys (bson.D fields) and Options
   - Map each to: {collection, keys: [{field, order}], unique: bool, name: string}

Store results:
  module.mongo_indexes_in_code = [
    {
      file: "service_repository.go",
      collection: "services",
      indexes: [
        {keys: [{"service_name": 1}], unique: true, name: ""},
        {keys: [{"tenant_id": 1, "service_name": 1}], unique: true, name: ""},
      ]
    }
  ]
```

---

## Step 2: Detect Existing Index Scripts

```text
Scan for existing MongoDB index scripts:

1. Glob tool: pattern "scripts/mongodb/*.js" OR "scripts/mongo/*.js"
2. For each script found:
   a. Extract collection name (from db.getCollection("name"))
   b. Extract index definitions (from both createIndex() and createIndexSafely() calls)
   c. Map each to: {file, collection, indexes: [{keys, options}]}

3. Also check for:
   - Makefile targets that reference mongosh or mongo scripts
   - Docker/docker-compose commands that run index scripts
   - CI/CD pipeline steps that execute index creation

Store results:
  existing_scripts = [
    {
      file: "scripts/mongodb/create-service-indexes.js",
      collection: "services",
      indexes: [
        {keys: {"tenant_id": 1}, name: "idx_tenant_id"},
        {keys: {"tenant_id": 1, "service_name": 1}, name: "idx_tenant_service_unique", unique: true},
      ]
    }
  ]
```

---

## Step 3: Cross-Reference and Identify Gaps

```text
Compare in-code indexes vs script indexes:

For each in-code index:
  - Find matching script index (same collection + same key fields)
  - If found → status: "covered"
  - If NOT found → status: "missing_script"

For each script index:
  - Find matching in-code index
  - If found → status: "covered"
  - If NOT found → status: "script_only" (index exists in script but not enforced in code)

Generate gap analysis:
  index_coverage = {
    covered: [{collection, keys, in_code_file, script_file}],
    missing_script: [{collection, keys, in_code_file}],  // needs script
    script_only: [{collection, keys, script_file}],       // extra scripts, no code match
  }
```

---

## Step 4: Generate Index Scripts for Missing Coverage

**Only if `missing_script` entries exist.**

For each missing index, generate a `mongosh`-compatible script following the dispatch layer pattern.

**Naming convention for generated scripts:**
- `scripts/mongodb/create-{collection}-indexes.js`
- If the `scripts/mongodb/` directory doesn't exist, create it.
- If a script already exists for that collection, create a new file with a numeric suffix (e.g., `create-{collection}-indexes-2.js`) to avoid modifying existing scripts. The original script remains untouched.

**Index naming convention:**
- Single field: `idx_{field}` (e.g., `idx_tenant_id`)
- Compound: `idx_{field1}_{field2}` (e.g., `idx_tenant_service`)
- Unique: append `_unique` (e.g., `idx_tenant_service_unique`)
- Nested fields: replace dots with underscores (e.g., `modules.name` → `idx_modules_name`)

### Script Template

```javascript
// MongoDB Index Creation Script for {Collection} Collection
// =====================================================
//
// Purpose:
//   Creates indexes for the '{collection}' collection detected from
//   in-code EnsureIndexes() in {source_file}.
//
// Usage:
//   mongosh "mongodb://localhost:27017/{database}" {script_path}
//
//   Or with authentication:
//   mongosh "mongodb://user:pass@host:port/{database}?authSource=admin" {script_path}
//
// Indexes Created:
//   {numbered list of indexes with descriptions}
//
// Notes:
//   - Script is idempotent (safe to run multiple times)
//   - Checks for existing indexes before creating
//   - Logs success/failure for each index
//
// =====================================================

// Helper function to safely create an index
function createIndexSafely(collection, keys, options) {
    // Compute fallback name from keys if options.name is not provided
    const indexName = options.name || Object.entries(keys).map(([k, v]) => `${k}_${v}`).join("_");
    options.name = indexName;
    const existingIndexes = collection.getIndexes();
    const indexExists = existingIndexes.some(idx => idx.name === indexName);

    if (indexExists) {
        print(`  [SKIP] Index '${indexName}' already exists`);
        return true;
    }

    try {
        collection.createIndex(keys, options);
        print(`  [OK] Index '${indexName}' created successfully`);
        return true;
    } catch (err) {
        print(`  [ERROR] Failed to create index '${indexName}': ${err.message}`);
        return false;
    }
}

// Main execution
print("");
print("=".repeat(60));
print("MongoDB Index Creation - {Collection} Collection");
print("=".repeat(60));
print("");

const coll = db.getCollection("{collection}");
print(`Database: ${db.getName()}`);
print(`Collection: {collection}`);
print("");
print("Creating indexes...");
print("");

let success = true;

// {For each detected index, generate a createIndexSafely call}
// Index N: {description based on keys and purpose}
success = createIndexSafely(coll,
    { "{field}": 1 },
    { name: "idx_{field}" }
) && success;

// ... repeat for each index ...

print("");
print("-".repeat(60));

if (success) {
    print("All indexes created/verified successfully");
} else {
    print("WARNING: Some indexes failed to create - review errors above");
}

print("");
print("Current indexes:");
print("");
const indexes = coll.getIndexes();
indexes.forEach(idx => {
    print(`  - ${idx.name}: ${JSON.stringify(idx.key)}${idx.unique ? " (unique)" : ""}`);
});
print("");
print("=".repeat(60));
print("Script completed");
print("=".repeat(60));
print("");
```

---

## Step 5: Upload Index Scripts to S3

**Execute after Step 4 (script generation) or when scripts already exist.**

Upload all index scripts to S3 so they are available for automated provisioning of dedicated tenant databases. Uses the AWS CLI installed on the local machine.

### Upload Flow

```text
1. Detect service name (from Phase 1 results)

2. Collect all index scripts:
   - Glob: scripts/mongodb/*.js OR scripts/mongo/*.js
   - If none found → skip upload, log warning

3. Verify AWS CLI is available:
   - Run: aws --version
   - If not found → SKIP Step 6: Log warning "AWS CLI not installed. Skipping S3 upload. Install with: brew install awscli"
     → Continue to Phase 4 report with upload status: "Skipped (AWS CLI not available)"

4. Ask the user which S3 bucket to use:
   "Found {N} index scripts to upload for service '{service_name}'.
    Which S3 bucket should I upload to?
    
    Example: my-bucket-name
    (scripts will be placed at: s3://{bucket}/scripts/mongodb/{service_name}/)"

   - Wait for user response
   - Store as: s3_bucket = "{user_response}"

5. Verify S3 access:
   - Run: aws s3 ls s3://{s3_bucket}/ 2>&1
   - If access denied → SKIP Step 6: Log warning "No access to bucket '{s3_bucket}'. Check AWS credentials (aws configure or aws sts get-caller-identity)"
     → Continue to Phase 4 report with upload status: "Failed (access denied)"
   - If bucket not found → SKIP Step 6: Log warning "Bucket '{s3_bucket}' not found."
     → Continue to Phase 4 report with upload status: "Failed (bucket not found)"

6. Upload each script (best-effort, continue on failure):
   - For each script in scripts/mongodb/*.js:
     aws s3 cp {script_path} s3://{s3_bucket}/scripts/mongodb/{service_name}/{filename} \
       --content-type "application/javascript"
   - If a single upload fails, log the error and continue with remaining files
   - Track: successful_uploads = [], failed_uploads = []

7. Verify upload:
   - Run: aws s3 ls s3://{s3_bucket}/scripts/mongodb/{service_name}/
   - List uploaded files with sizes
   - If count mismatches: list missing files (local - uploaded), report as "Partially uploaded ({X}/{Y})"

8. Report results:
   "Uploaded {N} index scripts to S3:
    ✅ s3://{s3_bucket}/scripts/mongodb/{service_name}/create-service-indexes.js
    ✅ s3://{s3_bucket}/scripts/mongodb/{service_name}/create-resource-indexes.js"
```

### Report Section Addition

Add to the Phase 4 HTML report:

```
┌──────────────────────────────────────────────────────┐
│ S3 Upload Status                                     │
├──────────────────────────┬───────────────────────────┤
│ Script                   │ Status                    │
├──────────────────────────┼───────────────────────────┤
│ create-service-indexes   │ ✅ Uploaded               │
│ create-resource-indexes  │ ✅ Uploaded               │
│ create-audit-indexes     │ ⚠️  Generated (not yet    │
│                          │    uploaded — run again)   │
└──────────────────────────┴───────────────────────────┘
S3 prefix: s3://{bucket}/scripts/mongodb/{service_name}/
```

---

## Report Section: MongoDB Index Coverage

Include this section in the Phase 4 HTML report when MongoDB indexes are detected.

### Table Format

```
┌──────────────────────────────────────────────────────────────┐
│ MongoDB Index Coverage                                       │
├──────────────┬────────────────────┬────────┬────────────────┤
│ Collection   │ Index Keys         │ Code   │ Script         │
├──────────────┼────────────────────┼────────┼────────────────┤
│ services     │ {service_name: 1}  │ ✅     │ ✅             │
│ services     │ {tenant_id: 1}     │ ❌     │ ✅ (extra)     │
│ services     │ {status: 1}        │ ❌     │ ✅ (extra)     │
│ audit_logs   │ {created_at: 1}    │ ✅     │ ❌ MISSING     │
└──────────────┴────────────────────┴────────┴────────────────┘

Legend:
  ✅ ✅  = Covered (in code + has script)
  ✅ ❌  = Missing script (generate one)
  ❌ ✅  = Script-only (no code match — review if still needed)
```

If there are **missing scripts**, show a callout:

```
⚠️  {N} indexes detected in code without corresponding scripts.
    Scripts will be generated automatically in scripts/mongodb/.
```

### Checklist Addition

For each module with MongoDB, add index status to the registration checklist:

```
- [ ] **Module:** `onboarding`
  - [ ] Resource: mongodb
  - [ ] MongoDB indexes: 3 in-code, 2 scripts (1 missing)
```
