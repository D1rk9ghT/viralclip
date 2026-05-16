import { initializeApp, getApps } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyAxE33oXPM4v4y94gEuvYoShCO8Pfm6guc",
  authDomain: "viral-clips-ai-9911-7f495.firebaseapp.com",
  projectId: "viral-clips-ai-9911",
  storageBucket: "viral-clips-ai-9911.firebasestorage.app",
  messagingSenderId: "893112851960",
  appId: "1:893112851960:web:676c6e4f77fcae7484ca0d",
  measurementId: "G-84BHD0JKPB"
};

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export { auth, googleProvider };
