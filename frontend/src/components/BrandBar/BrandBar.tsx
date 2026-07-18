import { Logo } from "../Logo/Logo";
import styles from "./BrandBar.module.scss";

/** Faixa de marca fixa no topo — persiste em todas as telas autenticadas
 * (renderizada uma vez em `App.tsx`, acima das rotas). */
export function BrandBar() {
    return (
        <div className={styles["bar"]}>
            <Logo size="sm" className={styles["logo"]} />
        </div>
    );
}

export default BrandBar;
