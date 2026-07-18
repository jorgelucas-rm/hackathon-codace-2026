import { useEffect, useState } from "react";
import { Screen } from "./types";
import Onboarding from "./pages/Onboarding/Onboarding";
import Login from "./pages/Login/Login";
import Home from "./pages/Home/Home";
import Courts from "./pages/Courts/Courts";
import CourtDetail from "./pages/CourtDetail/CourtDetail";
import Schedule from "./pages/Schedule/Schedule";
import Match from "./pages/Match/Match";
import Checkout from "./pages/Checkout/Checkout";
import Profile from "./pages/Profile/Profile";
import BottomNav from "./components/BottomNav/BottomNav";

function App() {
  const [screen, setScreen] = useState<Screen>("onboarding");
  const [selectedCourtId, setSelectedCourtId] = useState<number>(1);
  const [courtsSearch, setCourtsSearch] = useState("");
  const [courtsSportId, setCourtsSportId] = useState<number | null>(null);
  const [dark, setDark] = useState(false);

  const showNav = !["onboarding", "login", "signup"].includes(screen);
  const toggleDark = () => setDark((d) => !d);

  // O tema vive no <html> para que body e portais herdem as CSS variables
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  }, [dark]);

  return (
    <div>
      {screen === "onboarding" && <Onboarding onDone={() => setScreen("login")} />}
      {screen === "login" && <Login onLogin={() => setScreen("home")} />}
      {screen === "home" && (
        <Home
          onNavigate={setScreen}
          onSelectCourt={setSelectedCourtId}
          onSelectSport={(sportId) => { setCourtsSportId(sportId); setCourtsSearch(""); setScreen("courts"); }}
          onSearch={(term) => { setCourtsSearch(term); setCourtsSportId(null); setScreen("courts"); }}
          dark={dark}
          toggleDark={toggleDark}
        />
      )}
      {screen === "courts" && (
        <Courts
          onNavigate={setScreen}
          onSelectCourt={setSelectedCourtId}
          initialSearch={courtsSearch}
          initialSportId={courtsSportId}
        />
      )}
      {screen === "courtDetail" && <CourtDetail courtId={selectedCourtId} onNavigate={setScreen} />}
      {screen === "schedule" && <Schedule onNavigate={setScreen} />}
      {screen === "match" && <Match onNavigate={setScreen} />}
      {screen === "checkout" && <Checkout onNavigate={setScreen} />}
      {screen === "profile" && <Profile onNavigate={setScreen} />}
      {showNav && <BottomNav active={screen} onNavigate={setScreen} />}
    </div>
  );
}

export default App;
