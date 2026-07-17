import { SubmitEvent, useState } from "react";
import styles from "./Login.module.scss";

export function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
        event.preventDefault();
        // TODO: integrar com o backend
    }

    return (
        <div className="flex-center full-height">
            <form className={`card flex-column gap-md ${styles["form"]}`} onSubmit={handleSubmit}>
                <span className="title">Login</span>

                <div className="flex-column gap-sm">
                    <label htmlFor="email">E-mail</label>
                    <input
                        id="email"
                        className="input"
                        type="email"
                        placeholder="seu@email.com"
                        value={email}
                        onChange={(event) => setEmail(event.target.value)}
                        required
                    />
                </div>

                <div className="flex-column gap-sm">
                    <label htmlFor="password">Senha</label>
                    <input
                        id="password"
                        className="input"
                        type="password"
                        placeholder="********"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        required
                    />
                </div>

                <button className="btn" type="submit">Entrar</button>
            </form>
        </div>
    );
}

export default Login;
