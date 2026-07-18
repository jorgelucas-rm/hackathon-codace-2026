import { Navigate, Outlet } from "react-router-dom";
import { getAuthType } from "../../services/auth.service";
import { useAuth } from "../../contexts/AuthContext";

export function ProtectedRoute() {
    const { status } = useAuth();

    if (status === "loading") {
        return <div style={{ padding: 40, textAlign: "center" }}>Carregando...</div>;
    }

    if (status === "unauthenticated") {
        return <Navigate to="/login" replace />;
    }

    return <Outlet />;
}

// Guard das rotas do painel da empresa (/panel/*): além de autenticado, o
// token precisa ser de conta company — jogador logado volta para /home.
export function CompanyProtectedRoute() {
    const { status } = useAuth();

    if (status === "loading") {
        return <div style={{ padding: 40, textAlign: "center" }}>Carregando...</div>;
    }

    if (status === "unauthenticated") {
        return <Navigate to="/login" replace />;
    }

    if (getAuthType() !== "company") {
        return <Navigate to="/home" replace />;
    }

    return <Outlet />;
}

export default ProtectedRoute;
