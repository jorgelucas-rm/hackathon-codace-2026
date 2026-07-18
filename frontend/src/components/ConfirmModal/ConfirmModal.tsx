import React from "react";
import styles from "./ConfirmModal.module.scss";

interface ConfirmModalProps {
    open: boolean;
    icon?: React.ReactNode;
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    danger?: boolean;
    onConfirm: () => void;
    onCancel: () => void;
}

export function ConfirmModal({
    open,
    icon,
    title,
    message,
    confirmLabel = "Confirmar",
    cancelLabel = "Cancelar",
    danger = false,
    onConfirm,
    onCancel,
}: ConfirmModalProps) {
    if (!open) return null;

    return (
        <div className={styles["overlay"]} onClick={onCancel} role="dialog" aria-modal="true">
            <div className={styles["modal"]} onClick={(e) => e.stopPropagation()}>
                {icon && <div className={`${styles["icon"]} ${danger ? styles["icon-danger"] : ""}`}>{icon}</div>}
                <h2 className={styles["title"]}>{title}</h2>
                <p className={styles["message"]}>{message}</p>
                <div className={styles["actions"]}>
                    <button onClick={onCancel} className={styles["cancel"]}>{cancelLabel}</button>
                    <button onClick={onConfirm} className={`${styles["confirm"]} ${danger ? styles["confirm-danger"] : ""}`}>
                        {confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ConfirmModal;
