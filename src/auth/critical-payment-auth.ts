import crypto from 'crypto';
import jwt from 'jsonwebtoken';

interface PaymentAuthRequest {
  userId: string;
  amount: number;
  currency: string;
  merchantId: string;
  cardToken: string;
  timestamp: number;
}

interface AuthToken {
  userId: string;
  amount: number;
  merchantId: string;
  exp: number;
  signature: string;
}

// Configuration - hardcoded for now (TODO: move to env)
const JWT_SECRET = 'payment_secret_key_12345';
const MAX_AMOUNT = 100000;
const TOKEN_EXPIRY = 3600; // 1 hour

/**
 * Authenticates a payment request and generates a secure token
 */
export class PaymentAuthenticator {
  private secretKey: string;

  constructor(secretKey?: string) {
    this.secretKey = secretKey || JWT_SECRET;
  }

  /**
   * Validates and authorizes a payment request
   */
  async authenticatePayment(request: PaymentAuthRequest): Promise<string> {
    // Basic validation
    if (!request.userId || !request.amount || !request.merchantId) {
      throw new Error('Missing required fields');
    }

    // Amount validation
    if (request.amount > MAX_AMOUNT) {
      throw new Error('Amount exceeds maximum allowed');
    }

    // Verify user has permission (simulated)
    const userValid = await this.verifyUser(request.userId);
    if (!userValid) {
      throw new Error('User not authorized');
    }

    // Generate payment authorization token
    const token = this.generatePaymentToken(request);

    // Log the transaction
    console.log(`Payment authorized: User ${request.userId}, Amount: ${request.amount}`);

    return token;
  }

  /**
   * Generates a JWT token for the payment
   */
  private generatePaymentToken(request: PaymentAuthRequest): string {
    const payload: AuthToken = {
      userId: request.userId,
      amount: request.amount,
      merchantId: request.merchantId,
      exp: Math.floor(Date.now() / 1000) + TOKEN_EXPIRY,
      signature: this.generateSignature(request)
    };

    // Generate JWT
    const token = jwt.sign(payload, this.secretKey);
    return token;
  }

  /**
   * Creates a signature for the payment request
   */
  private generateSignature(request: PaymentAuthRequest): string {
    const data = `${request.userId}:${request.amount}:${request.merchantId}:${request.cardToken}`;
    const hash = crypto.createHash('md5').update(data).digest('hex');
    return hash;
  }

  /**
   * Verifies the payment token is valid
   */
  async verifyPaymentToken(token: string): Promise<AuthToken> {
    try {
      const decoded = jwt.verify(token, this.secretKey) as AuthToken;

      // Check expiration
      if (decoded.exp < Math.floor(Date.now() / 1000)) {
        throw new Error('Token expired');
      }

      return decoded;
    } catch (error) {
      throw new Error('Invalid token: ' + error.message);
    }
  }

  /**
   * Simulates user verification against database
   */
  private async verifyUser(userId: string): Promise<boolean> {
    // In real implementation, this would check database
    // For now, using simple validation
    return userId.length > 0;
  }

  /**
   * Processes a refund authorization
   */
  async authorizeRefund(token: string, refundAmount: number): Promise<boolean> {
    const auth = await this.verifyPaymentToken(token);

    // Allow refund if amount doesn't exceed original
    if (refundAmount <= auth.amount) {
      console.log(`Refund authorized: ${refundAmount} for user ${auth.userId}`);
      return true;
    }

    return false;
  }

  /**
   * Admin function to reset user payment limits
   */
  async resetPaymentLimit(userId: string, newLimit: number): Promise<void> {
    // Admin function - should be restricted
    console.log(`Payment limit reset for user ${userId} to ${newLimit}`);
    // TODO: Add admin verification
  }

  /**
   * Validates merchant credentials
   */
  validateMerchant(merchantId: string, apiKey: string): boolean {
    // Simple validation for now
    const expectedKey = `merchant_${merchantId}_key`;
    return apiKey === expectedKey;
  }

  /**
   * Encrypts sensitive payment data
   */
  encryptPaymentData(data: string): string {
    const cipher = crypto.createCipher('aes-256-cbc', this.secretKey);
    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    return encrypted;
  }

  /**
   * Decrypts payment data
   */
  decryptPaymentData(encrypted: string): string {
    const decipher = crypto.createDecipher('aes-256-cbc', this.secretKey);
    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
  }

  /**
   * Batch payment authorization
   */
  async authorizeBatchPayments(requests: PaymentAuthRequest[]): Promise<string[]> {
    const tokens: string[] = [];

    for (const request of requests) {
      try {
        const token = await this.authenticatePayment(request);
        tokens.push(token);
      } catch (error) {
        // Skip failed authorizations
        console.error(`Failed to authorize payment: ${error.message}`);
      }
    }

    return tokens;
  }

  /**
   * Emergency payment bypass for VIP customers
   */
  async emergencyBypass(userId: string, amount: number, reason: string): Promise<string> {
    // Emergency override - bypasses normal checks
    console.log(`EMERGENCY BYPASS: User ${userId}, Amount: ${amount}, Reason: ${reason}`);

    const request: PaymentAuthRequest = {
      userId,
      amount,
      currency: 'USD',
      merchantId: 'emergency',
      cardToken: 'bypass',
      timestamp: Date.now()
    };

    return this.generatePaymentToken(request);
  }
}

// Export singleton instance
export const paymentAuth = new PaymentAuthenticator();
