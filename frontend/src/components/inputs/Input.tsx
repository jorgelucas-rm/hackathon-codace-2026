import styles from "./Input.module.scss";
import React from "react";


interface InputProps {
    type?: "email" | "password" | "text" | "tel",
    placeholder?: string,
    value?: string,
    onChange?: (value: string) => void,
    icon?: React.ReactNode,
    rightEl?: React.ReactNode,
    disabled?: boolean,
}


export const Input: React.FC<InputProps> = ({ type = "text", placeholder, value, onChange, icon, rightEl, disabled }) => {

    return (
        <div className={styles["wrapper"]}>
            {icon && <span className={styles["icon"]}>{icon}</span>}
            <input
                type={type}
                placeholder={placeholder}
                value={value}
                onChange={(e) => onChange?.(e.target.value)}
                disabled={disabled}
                readOnly={!onChange}
                className={`${styles["input"]} ${icon ? styles["with-icon"] : ""}`}
            />
            {rightEl && <span className={styles["right"]}>{rightEl}</span>}
        </div>
    )
}

export default Input;
