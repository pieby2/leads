import { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import GoogleProvider from 'next-auth/providers/google';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://vidcompare-backend.onrender.com';

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.YOUTUBE_CLIENT_ID || '',
      clientSecret: process.env.YOUTUBE_CLIENT_SECRET || '',
      authorization: {
        params: {
          scope: 'openid email profile https://www.googleapis.com/auth/youtube.readonly'
        }
      }
    }),
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        try {
          const formData = new URLSearchParams();
          formData.append('username', credentials.email);
          formData.append('password', credentials.password);

          const res = await fetch(`${API_BASE}/api/auth/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
          });

          if (!res.ok) {
            return null;
          }

          const user = await res.json();
          if (user && user.access_token) {
            return {
              id: user.user?.id || user.id || '1',
              email: credentials.email,
              accessToken: user.access_token
            };
          }
          return null;
        } catch (e) {
          console.error('Login error', e);
          return null;
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user, account }) {
      // If logging in with Google, swap it for a FastAPI token
      if (account && account.provider === 'google' && user?.email) {
        try {
          const res = await fetch(`${API_BASE}/api/auth/google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: user.email }),
          });
          if (res.ok) {
            const data = await res.json();
            token.accessToken = data.access_token;
            token.youtubeAccessToken = account.access_token; // Store Google token for YouTube Data API
          }
        } catch (e) {
          console.error('Google backend auth error', e);
        }
      } else if (user) {
        // Standard credentials login
        token.accessToken = (user as any).accessToken;
      }
      return token;
    },
    async session({ session, token }) {
      (session as any).accessToken = token.accessToken;
      (session as any).youtubeAccessToken = token.youtubeAccessToken;
      return session;
    }
  },
  pages: {
    signIn: '/login',
  },
  session: {
    strategy: 'jwt'
  }
};
