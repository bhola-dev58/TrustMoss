import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || 'AIzaSyCLc5RP4jxqwaQU9mWfVJYlwdAiUOOdWLQ',
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || 'trustmoss-app.firebaseapp.com',
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || 'trustmoss-app',
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || 'trustmoss-app.firebasestorage.app',
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || '200968222318',
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || '1:200968222318:web:a267f169b27d79e1f1587f',
};

// Initialize Firebase safely for Next.js SSR and client
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

// Request basic profile and email
googleProvider.setCustomParameters({
  prompt: 'select_account',
});

export { app, auth, googleProvider };
