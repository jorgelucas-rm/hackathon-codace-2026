import styles from "./Logo.module.scss";

interface LogoProps {
    size?: "sm" | "md" | "lg";
    className?: string;
}

export function Logo({ size = "md", className }: LogoProps) {
    return (
        <span className={`${styles["logo"]} ${styles[`logo-${size}`]} ${className ?? ""}`}>
            Reserva<span className={styles["highlight"]}>ê</span>
        </span>
    );
}

export default Logo;
