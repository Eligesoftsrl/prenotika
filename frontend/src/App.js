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
import Clienti from "@/pages/Clienti";
import Orari from "@/pages/Orari";
import Appuntamenti from "@/pages/Appuntamenti";
import Studios from "@/pages/Studios";

function RootRedirect() {
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
            <Route path="/login" element={<Login />} />
            <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route path="/dashboard" element={<ProtectedRoute roles={["admin", "docente"]}><Dashboard /></ProtectedRoute>} />
              <Route path="/docenti" element={<ProtectedRoute roles={["admin"]}><Docenti /></ProtectedRoute>} />
              <Route path="/docenti/:id/alunni" element={<ProtectedRoute roles={["admin"]}><DocenteAlunni /></ProtectedRoute>} />
              <Route path="/docenti/:id/materie" element={<ProtectedRoute roles={["admin"]}><DocenteMaterie /></ProtectedRoute>} />
              <Route path="/materie" element={<ProtectedRoute roles={["admin", "docente"]}><Materie /></ProtectedRoute>} />
              <Route path="/clienti" element={<ProtectedRoute roles={["admin", "docente"]}><Clienti /></ProtectedRoute>} />
              <Route path="/orari" element={<ProtectedRoute roles={["admin", "docente"]}><Orari /></ProtectedRoute>} />
              <Route path="/appuntamenti" element={<ProtectedRoute roles={["admin", "docente"]}><Appuntamenti /></ProtectedRoute>} />
              <Route path="/studios" element={<ProtectedRoute roles={["super_admin"]}><Studios /></ProtectedRoute>} />
            </Route>
            <Route path="/" element={<RootRedirect />} />
            <Route path="*" element={<RootRedirect />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
