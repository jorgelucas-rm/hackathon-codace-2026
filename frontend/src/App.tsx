import { useEffect, useRef, useState } from "react";
import {
    Navigate,
    Route,
    Routes,
    useLocation,
    useNavigate,
    useParams,
    useSearchParams,
} from "react-router-dom";
import { Screen } from "./types";
import Onboarding from "./pages/Onboarding/Onboarding";
import Login from "./pages/Login/Login";
import Home from "./pages/Home/Home";
import Courts from "./pages/Courts/Courts";
import CourtDetail from "./pages/CourtDetail/CourtDetail";
import Schedule from "./pages/Schedule/Schedule";
import Match from "./pages/Match/Match";
import OpenMatches from "./pages/OpenMatches/OpenMatches";
import Checkout from "./pages/Checkout/Checkout";
import Profile from "./pages/Profile/Profile";
import Account from "./pages/Account/Account";
import CompanyPanel, { PANEL_TABS, PanelTab } from "./pages/CompanyPanel/CompanyPanel";
import BottomNav from "./components/BottomNav/BottomNav";
import BrandBar from "./components/BrandBar/BrandBar";
import ProtectedRoute, { CompanyProtectedRoute } from "./components/ProtectedRoute/ProtectedRoute";
import { getAuthType } from "./services/auth.service";
import { AuthProvider, useAuth } from "./contexts/AuthContext";

const NAV_PATHS = ["/home", "/courts", "/schedule", "/match", "/open-matches", "/checkout", "/profile"];

function pathToScreen(pathname: string): Screen {
    if (pathname.startsWith("/courts/")) return "courtDetail";
    if (pathname.startsWith("/courts")) return "courts";
    if (pathname.startsWith("/schedule")) return "schedule";
    if (pathname.startsWith("/open-matches")) return "openMatches";
    if (pathname.startsWith("/match")) return "match";
    if (pathname.startsWith("/checkout")) return "checkout";
    if (pathname.startsWith("/account")) return "account";
    if (pathname.startsWith("/profile")) return "profile";
    return "home";
}

// Destino padrão de quem já está logado: empresa cai no painel, jogador na home.
function loggedInHome(): string {
    return getAuthType() === "company" ? "/panel" : "/home";
}

// Decide a tela inicial ("/") com base na sessão já validada pelo AuthContext.
function RootRedirect() {
    const { status } = useAuth();
    if (status === "loading") return <div style={{ padding: 40, textAlign: "center" }}>Carregando...</div>;
    return <Navigate to={status === "authenticated" ? loggedInHome() : "/onboarding"} replace />;
}

// Usuário já logado não deve ver a tela de login de novo.
function LoginRoute({ onLogin }: { onLogin: () => void }) {
    const { status } = useAuth();
    if (status === "authenticated") return <Navigate to={loggedInHome()} replace />;
    return <Login onLogin={onLogin} />;
}

// /panel/:tab — valida a aba e injeta a navegação entre abas do painel.
function CompanyPanelRoute() {
    const { tab } = useParams();
    const navigate = useNavigate();
    if (!tab || !PANEL_TABS.includes(tab as PanelTab)) {
        return <Navigate to="/panel/agenda" replace />;
    }
    return <CompanyPanel tab={tab as PanelTab} onChangeTab={(t) => navigate(`/panel/${t}`)} />;
}

function CourtsRoute({ onNavigate, onSelectCourt }: {
    onNavigate: (screen: Screen) => void;
    onSelectCourt: (id: number) => void;
}) {
    const [params] = useSearchParams();
    const q = params.get("q") ?? "";
    const sportId = params.get("sportId");
    return (
        <Courts
            onNavigate={onNavigate}
            onSelectCourt={onSelectCourt}
            initialSearch={q}
            initialSportId={sportId ? Number(sportId) : null}
        />
    );
}

function CourtDetailRoute({ onNavigate, onSelectSchedule }: {
    onNavigate: (screen: Screen) => void;
    onSelectSchedule: (courtId: number) => void;
}) {
    const { courtId } = useParams();
    return <CourtDetail courtId={Number(courtId)} onNavigate={onNavigate} onSelectSchedule={onSelectSchedule} />;
}

function ScheduleRoute({ onNavigate, onBookingCreated }: {
    onNavigate: (screen: Screen) => void;
    onBookingCreated: (paymentId: number) => void;
}) {
    const { courtId } = useParams();
    return (
        <Schedule
            courtId={courtId ? Number(courtId) : null}
            onNavigate={onNavigate}
            onBookingCreated={onBookingCreated}
        />
    );
}

function CheckoutRoute({ onNavigate }: { onNavigate: (screen: Screen) => void }) {
    const { paymentId } = useParams();
    return <Checkout paymentId={paymentId ? Number(paymentId) : null} onNavigate={onNavigate} />;
}

function AppShell() {
    const navigate = useNavigate();
    const location = useLocation();
    const auth = useAuth();
    const [dark, setDark] = useState(false);
    // Ref (não state) porque `onSelectCourt` e o `onNavigate("courtDetail")` que o
    // segue são disparados no mesmo clique — um state só refletiria o novo valor
    // no próximo render, tarde demais para montar a URL de destino.
    const selectedCourtIdRef = useRef<number>(1);

    const showNav = NAV_PATHS.some((p) => location.pathname === p || location.pathname.startsWith(`${p}/`));
    const toggleDark = () => setDark((d) => !d);

    // O tema vive no <html> para que body e portais herdem as CSS variables
    useEffect(() => {
        document.documentElement.dataset.theme = dark ? "dark" : "light";
    }, [dark]);

    function onNavigate(screen: Screen) {
        if (screen === "courtDetail") {
            navigate(`/courts/${selectedCourtIdRef.current}`);
            return;
        }
        if (screen === "openMatches") {
            navigate("/open-matches");
            return;
        }
        navigate(`/${screen}`);
    }

    function onSelectCourt(id: number) {
        selectedCourtIdRef.current = id;
    }

    function onSearch(term: string) {
        navigate(`/courts?q=${encodeURIComponent(term)}`);
    }

    function onSelectSport(sportId: number) {
        navigate(`/courts?sportId=${sportId}`);
    }

    function onSelectSchedule(courtId: number) {
        navigate(`/schedule/${courtId}`);
    }

    function onBookingCreated(paymentId: number) {
        navigate(`/checkout/${paymentId}`);
    }

    function onOpenAppointment(kind: "booking" | "group", id: number) {
        navigate(kind === "booking" ? `/match?bookingId=${id}` : `/match?groupId=${id}`);
    }

    function onLogin() {
        auth.refresh();
        // Empresa vai direto para o painel; jogador segue para a home.
        navigate(loggedInHome());
    }

    return (
        <div>
            {showNav && <BrandBar />}
            <Routes>
                <Route path="/" element={<RootRedirect />} />
                <Route path="/onboarding" element={<Onboarding onDone={() => navigate("/login")} />} />
                <Route path="/login" element={<LoginRoute onLogin={onLogin} />} />

                <Route element={<ProtectedRoute />}>
                    <Route
                        path="/home"
                        element={(
                            <Home
                                onNavigate={onNavigate}
                                onSelectCourt={onSelectCourt}
                                onSelectSport={onSelectSport}
                                onSearch={onSearch}
                                onGroupJoined={onBookingCreated}
                                onOpenAppointment={onOpenAppointment}
                                dark={dark}
                                toggleDark={toggleDark}
                            />
                        )}
                    />
                    <Route path="/courts" element={<CourtsRoute onNavigate={onNavigate} onSelectCourt={onSelectCourt} />} />
                    <Route
                        path="/courts/:courtId"
                        element={<CourtDetailRoute onNavigate={onNavigate} onSelectSchedule={onSelectSchedule} />}
                    />
                    <Route path="/schedule" element={<ScheduleRoute onNavigate={onNavigate} onBookingCreated={onBookingCreated} />} />
                    <Route
                        path="/schedule/:courtId"
                        element={<ScheduleRoute onNavigate={onNavigate} onBookingCreated={onBookingCreated} />}
                    />
                    <Route path="/match" element={<Match onNavigate={onNavigate} />} />
                    <Route
                        path="/open-matches"
                        element={<OpenMatches onNavigate={onNavigate} onGroupJoined={onBookingCreated} />}
                    />
                    <Route path="/checkout" element={<CheckoutRoute onNavigate={onNavigate} />} />
                    <Route path="/checkout/:paymentId" element={<CheckoutRoute onNavigate={onNavigate} />} />
                    <Route path="/profile" element={<Profile onNavigate={onNavigate} />} />
                    <Route path="/account" element={<Account onNavigate={onNavigate} />} />
                </Route>

                <Route element={<CompanyProtectedRoute />}>
                    <Route path="/panel" element={<Navigate to="/panel/agenda" replace />} />
                    <Route path="/panel/:tab" element={<CompanyPanelRoute />} />
                </Route>

                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            {showNav && <BottomNav active={pathToScreen(location.pathname)} onNavigate={onNavigate} />}
        </div>
    );
}

function App() {
    return (
        <AuthProvider>
            <AppShell />
        </AuthProvider>
    );
}

export default App;
