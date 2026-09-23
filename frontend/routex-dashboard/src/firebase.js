import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyBZLjZHX8nNZDgw-7V6G4oQAYpdwOZdJuw",
  authDomain: "routex-auth.firebaseapp.com",
  projectId: "routex-auth",
  storageBucket: "routex-auth.firebasestorage.app",
  messagingSenderId: "248566615637",
  appId: "1:248566615637:web:7427276e38001c6e1acedc"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
