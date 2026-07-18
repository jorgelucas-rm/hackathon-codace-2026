import { Navigate, Outlet } from "react-router-dom";
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

export default ProtectedRoute;
