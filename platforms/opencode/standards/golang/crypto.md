## Crypto (commons/crypto)

Sensitive data storage **MUST** use `ccrypto` for encryption and hashing.

```go
// AES-GCM encryption for sensitive fields
crypto := &ccrypto.Crypto{Key: os.Getenv("ENCRYPTION_KEY")}
if err := crypto.InitializeCipher(); err != nil {
    return err
}

encrypted, err := crypto.Encrypt(&plainText)
decrypted, err := crypto.Decrypt(&encrypted)

// HMAC-SHA256 hashing (for fingerprints, cache keys)
hash := crypto.GenerateHash(&value)
```

---

