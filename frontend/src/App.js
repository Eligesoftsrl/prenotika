import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Docenti from "@/pages/Docenti";
import DocenteAlunni from "@/pages/DocenteAlunni";
import DocenteMaterie from "@/pages/DocenteMaterie";
import Materie from "@/pages/Materie";
import Impostazioni from "@/pages/Impostazioni";
import Report from "@/pages/Report";
import Clienti from "@/pages/Clienti";
import Orari from "@/pages/Orari";
import Appuntamenti from "@/pages/Appuntamenti";
import NuovoAppuntamento from "@/pages/NuovoAppuntamento";
import Studios from "@/pages/Studios";
import Landing from "@/pages/Landing";
import Eccezioni from "@/pages/Eccezioni";
import Leads from "@/pages/Leads";

function AppRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center text-[color:var(--text-2)]">Caricamento…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "super_admin") return <Navigate to="/studios" replace />;
  return <Navigate to="/dashboard" replace />;
}

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/app" element={<AppRedirect />} />
            <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route path="/dashboard" element={<ProtectedRoute roles={["admin", "docente"]}><Dashboard /></ProtectedRoute>} />
              <Route path="/docenti" element={<ProtectedRoute roles={["admin"]}><Docenti /></ProtectedRoute>} />
              <Route path="/docenti/:id/alunni" element={<ProtectedRoute roles={["admin"]}><DocenteAlunni /></ProtectedRoute>} />
              <Route path="/docenti/:id/materie" element={<ProtectedRoute roles={["admin"]}><DocenteMaterie /></ProtectedRoute>} />
              <Route path="/materie" element={<ProtectedRoute roles={["admin", "docente"]}><Materie /></ProtectedRoute>} />
              <Route path="/impostazioni" element={<ProtectedRoute roles={["admin"]}><Impostazioni /></ProtectedRoute>} />
              <Route path="/report" element={<ProtectedRoute roles={["admin"]}><Report /></ProtectedRoute>} />
              <Route path="/clienti" element={<ProtectedRoute roles={["admin", "docente"]}><Clienti /></ProtectedRoute>} />
              <Route path="/orari" element={<ProtectedRoute roles={["admin", "docente"]}><Orari /></ProtectedRoute>} />
              <Route path="/eccezioni" element={<ProtectedRoute roles={["admin", "docente"]}><Eccezioni /></ProtectedRoute>} />
              <Route path="/appuntamenti" element={<ProtectedRoute roles={["admin", "docente"]}><Appuntamenti /></ProtectedRoute>} />
              <Route path="/appuntamenti/nuovo" element={<ProtectedRoute roles={["admin", "docente"]}><NuovoAppuntamento /></ProtectedRoute>} />
              <Route path="/studios" element={<ProtectedRoute roles={["super_admin"]}><Studios /></ProtectedRoute>} />
              <Route path="/leads" element={<ProtectedRoute roles={["super_admin"]}><Leads /></ProtectedRoute>} />
            </Route>
            <Route path="*" element={<AppRedirect />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
