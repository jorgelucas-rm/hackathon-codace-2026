import styles from "./Logo.module.scss";

interface LogoProps {
    size?: "sm" | "md" | "lg";
}

export function Logo({ size = "md" }: LogoProps) {
    return (
        <span className={`${styles["logo"]} ${styles[`logo-${size}`]}`}>
            Reserva<span className={styles["highlight"]}>ê</span>
        </span>
    );
}

export default Logo;
