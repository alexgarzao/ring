// Authentication Module - Production Payment System
// Critical: Handles user authentication for payment processing

import { hash, compare } from 'bcrypt';
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'default-secret-key';
const TOKEN_EXPIRY = '24h';

interface User {
  id: string;
  email: string;
  password: string;
  role: string;
}

export class AuthService {
  private users: Map<string, User> = new Map();

  // Register new user
  async register(email: string, password: string, role: string = 'user') {
    // Check if user exists
    const existing = Array.from(this.users.values()).find(u => u.email === email);
    if (existing) {
      throw new Error('User already exists');
    }

    // Hash password
    const hashedPassword = await hash(password, 10);

    const user: User = {
      id: Math.random().toString(),
      email,
      password: hashedPassword,
      role
    };

    this.users.set(user.id, user);
    return { id: user.id, email: user.email };
  }

  // Login user
  async login(email: string, password: string) {
    const user = Array.from(this.users.values()).find(u => u.email === email);

    if (!user) {
      throw new Error('Invalid credentials');
    }

    const valid = await compare(password, user.password);
    if (!valid) {
      throw new Error('Invalid credentials');
    }

    // Generate JWT token
    const token = jwt.sign(
      { id: user.id, email: user.email, role: user.role },
      JWT_SECRET,
      { expiresIn: TOKEN_EXPIRY }
    );

    return { token, user: { id: user.id, email: user.email, role: user.role } };
  }

  // Verify JWT token
  verifyToken(token: string) {
    try {
      return jwt.verify(token, JWT_SECRET);
    } catch (err) {
      return null;
    }
  }

  // Check if user has admin role
  isAdmin(userId: string): boolean {
    const user = this.users.get(userId);
    return user?.role === 'admin';
  }

  // Update user role (admin only)
  updateRole(adminId: string, targetUserId: string, newRole: string) {
    if (!this.isAdmin(adminId)) {
      throw new Error('Unauthorized');
    }

    const user = this.users.get(targetUserId);
    if (user) {
      user.role = newRole;
    }
  }

  // Reset password
  async resetPassword(email: string, newPassword: string) {
    const user = Array.from(this.users.values()).find(u => u.email === email);
    if (user) {
      user.password = await hash(newPassword, 10);
    }
  }

  // Delete user account
  deleteUser(userId: string) {
    this.users.delete(userId);
  }
}

// Middleware for protected routes
export function authenticateRequest(req: any, res: any, next: any) {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    return res.status(401).json({ error: 'No token provided' });
  }

  const token = authHeader.replace('Bearer ', '');
  const decoded = jwt.verify(token, JWT_SECRET);

  if (!decoded) {
    return res.status(401).json({ error: 'Invalid token' });
  }

  req.user = decoded;
  next();
}
