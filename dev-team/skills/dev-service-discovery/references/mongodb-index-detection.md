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
   - Grep tool: pattern "func.*EnsureIndexes\|IndexModel\|CreateIndex\|createIndex"
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
SCAN for existing MongoDB index scripts:

1. Glob tool: pattern "scripts/mongodb/*.js" OR "scripts/mongo/*.js"
2. For each script found:
   a. Extract collection name (from db.getCollection("name"))
   b. Extract index definitions (from createIndex calls)
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
COMPARE in-code indexes vs script indexes:

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

For each missing index, generate a `mongosh`-compatible script following the tenant-manager pattern.

**Naming convention for generated scripts:**
- `scripts/mongodb/create-{collection}-indexes.js`
- If the `scripts/mongodb/` directory doesn't exist, create it.
- If a script already exists for that collection, append the new indexes to it instead of creating a new file.

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
    const indexName = options.name;
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

## Step 5: Execute Index Scripts (Optional — User Confirmation Required)

**⚠️ NEVER execute without explicit user confirmation.**

If the user requests execution of detected or generated index scripts:

```text
1. Determine MongoDB connection:
   a. Check environment variables: MONGO_URI, MONGO_HOST, MONGO_PORT, MONGO_DATABASE
   b. Check bootstrap config: grep "MongoURI\|MongoHost\|MongoDB" in internal/bootstrap/config.go
   c. Check docker-compose.yml for MongoDB service + port mapping
   d. Default fallback: mongodb://localhost:27017/{service_name}

2. List scripts to execute:
   - All files in scripts/mongodb/*.js (sorted alphabetically)
   - Show the user each script + target database

3. ASK for confirmation:
   "Found {N} index scripts for database '{db_name}':
    1. scripts/mongodb/create-service-indexes.js (4 indexes)
    2. scripts/mongodb/create-resource-indexes.js (4 indexes)
   
    Target: mongodb://localhost:27017/{db_name}
    
    Execute? [y/N]"

4. Execute with mongosh:
   mongosh "{connection_string}" scripts/mongodb/{script}.js

5. Report results per script (OK/SKIP/ERROR per index)
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
    Run with --generate-scripts to create them.
```

### Checklist Addition

For each module with MongoDB, add index status to the registration checklist:

```
- [ ] **Module:** `onboarding`
  - [ ] Resource: mongodb
  - [ ] MongoDB indexes: 3 in-code, 2 scripts (1 missing)
```
