import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import readline from "readline-sync";
import { GoogleGenerativeAI } from "@google/generative-ai";

dotenv.config();
// Carga API KEY desde variable de entorno
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: "models/gemini-2.5-flash" });

async function editFile() {
  console.log("🛠  Editor de archivos con Gemini");

  // 1. Ruta del archivo a modificar
  const filePath = readline.question("Ruta del archivo a modificar: ");

  if (!fs.existsSync(filePath)) {
    console.log("❌ El archivo no existe.");
    return;
  }

  const original = fs.readFileSync(filePath, "utf8");

  // 2. Qué quieres que haga Gemini
  const instruction = readline.question("¿Qué quieres que Gemini modifique? ");

  console.log("\n⏳ Procesando...");
  
  // 3. Enviar a Gemini
  const prompt = `
Eres un asistente experto en programación. A continuación tienes un archivo completo.
Tu tarea es MODIFICARLO EXACTAMENTE como pide el usuario y devolver SOLO el código final.

--- ARCHIVO ORIGINAL ---
${original}

--- INSTRUCCIÓN DEL USUARIO ---
${instruction}

Devuelve ÚNICAMENTE el archivo completo modificado, sin explicaciones.
`;

  const result = await model.generateContent(prompt);
  const modified = result.response.text();

  // 4. Guardar el archivo
  fs.writeFileSync(filePath, modified, "utf8");

  console.log("\n✅ Archivo modificado exitosamente.");
}

editFile();
