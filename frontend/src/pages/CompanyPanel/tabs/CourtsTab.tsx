import { useState } from "react";
import { Loader2, Trash2 } from "lucide-react";
import { ApiError, PanelCourt, formatPriceCents } from "../../../services/companyPanel.service";
import { useSports } from "../../../hooks/useCompanies";
import { ConfirmModal } from "../../../components/ConfirmModal/ConfirmModal";
import { useCreateCourt, useDeleteCourt, useMyCourts, useUpdateCourt } from "../hooks/useCompanyPanel";
import { centsToReaisInput, parsePriceToCents } from "../panelUtils";
import styles from "../CompanyPanel.module.scss";

type CourtModalState =
    | { mode: "create" }
    | { mode: "edit"; court: PanelCourt }
    | null;

export function CourtsTab() {
    const { data: courts, isLoading, isError } = useMyCourts();
    const [modal, setModal] = useState<CourtModalState>(null);

    return (
        <>
            <div className={styles["tab-head"]}>
                <div>
                    <div className={styles["eyebrow"]}>Estrutura</div>
                    <div className={styles["tab-title"]}>Minhas quadras</div>
                </div>
                <button className={styles["primary-btn"]} onClick={() => setModal({ mode: "create" })}>
                    + Nova quadra
                </button>
            </div>

            {isLoading && (
                <div className={styles["state-msg"]}><Loader2 width={18} height={18} /> Carregando quadras...</div>
            )}
            {isError && !isLoading && (
                <div className={`${styles["state-msg"]} ${styles["state-error"]}`}>Erro ao carregar as quadras. Tente novamente.</div>
            )}
            {!isLoading && !isError && (courts ?? []).length === 0 && (
                <div className={styles["state-msg"]}>Nenhuma quadra cadastrada ainda — comece pela primeira.</div>
            )}

            <div className={styles["courts-grid"]}>
                {(courts ?? []).map((court) => {
                    const active = court.status === "ACTIVE";
                    return (
                        <button
                            key={court.id}
                            className={`${styles["court-card"]} ${active ? "" : styles["court-card-inactive"]}`}
                            onClick={() => setModal({ mode: "edit", court })}
                        >
                            <div className={styles["court-top"]}>
                                <div className={styles["court-name"]}>{court.name}</div>
                                <span className={`${styles["status-pill"]} ${active ? styles["status-active"] : styles["status-inactive"]}`}>
                                    {active ? "Ativa" : "Inativa"}
                                </span>
                            </div>
                            <div className={styles["court-meta"]}>
                                {court.sports.map((s) => s.name).join(" · ") || "Sem esportes"} · até {court.capacity} pessoas
                            </div>
                            <div className={styles["court-foot"]}>
                                <div className={styles["court-price"]}>{formatPriceCents(court.base_price_hour)}/h</div>
                                <span className={styles["court-edit"]}>Editar →</span>
                            </div>
                        </button>
                    );
                })}
            </div>
            {modal && <CourtModal modal={modal} onClose={() => setModal(null)} />}
        </>
    );
}

// ---------------------------------------------------------------------------
// Modal criar/editar quadra
// ---------------------------------------------------------------------------

function CourtModal({ modal, onClose }: { modal: NonNullable<CourtModalState>; onClose: () => void }) {
    const editing = modal.mode === "edit" ? modal.court : null;

    const [name, setName] = useState(editing?.name ?? "");
    const [cap, setCap] = useState(editing ? String(editing.capacity) : "10");
    const [priceReais, setPriceReais] = useState(
        editing ? centsToReaisInput(editing.base_price_hour) : "80,00"
    );
    const [sportIds, setSportIds] = useState<number[]>(editing ? editing.sports.map((s) => s.id) : []);
    const [error, setError] = useState("");

    const [confirmDelete, setConfirmDelete] = useState(false);
    const [confirmForce, setConfirmForce] = useState(false);

    const { data: sports } = useSports();
    const createMutation = useCreateCourt();
    const updateMutation = useUpdateCourt();
    const deleteMutation = useDeleteCourt();
    const pending = createMutation.isPending || updateMutation.isPending || deleteMutation.isPending;

    const toggleSport = (id: number) => {
        setSportIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
    };

    const submit = () => {
        const capacity = parseInt(cap, 10);
        const cents = parsePriceToCents(priceReais);
        if (!name.trim()) { setError("Informe o nome da quadra."); return; }
        if (!capacity || capacity < 1) { setError("Capacidade inválida."); return; }
        if (cents === null) { setError("Preço inválido — use o formato 80,00."); return; }
        setError("");

        const options = { onSuccess: onClose, onError: (e: Error) => setError(e.message) };
        if (editing) {
            updateMutation.mutate(
                {
                    courtId: editing.id,
                    dto: { name: name.trim(), capacity, base_price_hour: cents, sport_ids: sportIds },
                },
                options
            );
        } else {
            createMutation.mutate(
                { name: name.trim(), capacity, base_price_hour: cents, sport_ids: sportIds },
                options
            );
        }
    };

    const toggleStatus = () => {
        if (!editing) return;
        setError("");
        updateMutation.mutate(
            {
                courtId: editing.id,
                dto: { status: editing.status === "ACTIVE" ? "INACTIVE" : "ACTIVE" },
            },
            { onSuccess: onClose, onError: (e: Error) => setError(e.message) }
        );
    };

    const remove = (force: boolean) => {
        if (!editing) return;
        setError("");
        deleteMutation.mutate(
            { courtId: editing.id, force },
            {
                onSuccess: () => {
                    setConfirmDelete(false);
                    setConfirmForce(false);
                    onClose();
                },
                onError: (e: ApiError) => {
                    setConfirmDelete(false);
                    // 409 = quadra tem reservas: oferece exclusão permanente (cascata).
                    if (!force && e.code === "CONFLICT") {
                        setConfirmForce(true);
                    } else {
                        setConfirmForce(false);
                        setError(e.message);
                    }
                },
            }
        );
    };

    return (
        <div className={styles["modal-overlay"]} onClick={onClose} role="dialog" aria-modal="true">
            <div className={styles["modal"]} onClick={(e) => e.stopPropagation()}>
                <div className={styles["modal-eyebrow"]}>{editing ? "Editar quadra" : "Nova quadra"}</div>
                <div className={styles["modal-title"]}>{editing ? editing.name : "Cadastrar quadra"}</div>

                <label className={styles["field-label"]}>Nome da quadra</label>
                <input
                    className={styles["modal-input"]}
                    placeholder="ex.: Quadra 1 – Beach Tênis"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />

                <div className={styles["modal-row"]}>
                    <div>
                        <label className={styles["field-label"]}>Capacidade</label>
                        <input className={styles["modal-input"]} value={cap} onChange={(e) => setCap(e.target.value)} />
                    </div>
                    <div>
                        <label className={styles["field-label"]}>Preço/hora (R$)</label>
                        <input className={styles["modal-input"]} value={priceReais} onChange={(e) => setPriceReais(e.target.value)} />
                    </div>
                </div>
                <div className={styles["modal-hint"]}>Enviado ao sistema em centavos (R$ 80,00 → 8000).</div>

                <label className={`${styles["field-label"]} ${styles["field-gap"]}`} style={{ marginBottom: 6 }}>
                    Esportes atendidos
                </label>
                <div className={styles["sport-chips"]}>
                    {(sports ?? []).map((sport) => {
                        const selected = sportIds.includes(sport.id);
                        return (
                            <button
                                key={sport.id}
                                className={`${styles["sport-chip"]} ${selected ? styles["sport-chip-active"] : ""}`}
                                onClick={() => toggleSport(sport.id)}
                            >
                                {sport.name}
                            </button>
                        );
                    })}
                    {(sports ?? []).length === 0 && (
                        <span className={styles["modal-hint"]}>Carregando esportes...</span>
                    )}
                </div>

                {error && <p className={styles["form-error"]}>{error}</p>}

                <button className={styles["modal-primary-btn"]} onClick={submit} disabled={pending}>
                    {pending ? "Salvando..." : editing ? "Salvar alterações" : "Criar quadra"}
                </button>

                {editing && (
                    <>
                        <button className={styles["subtle-btn"]} onClick={toggleStatus} disabled={pending}>
                            {editing.status === "ACTIVE" ? "Desativar quadra (arquivar)" : "Reativar quadra"}
                        </button>
                        <div className={styles["modal-hint-center"]}>
                            Desativar = arquivar. A quadra some da busca, o histórico fica — e dá pra reativar depois.
                        </div>
                        <button className={styles["delete-btn"]} onClick={() => setConfirmDelete(true)} disabled={pending}>
                            <Trash2 width={16} height={16} /> Excluir quadra
                        </button>
                        <div className={styles["modal-hint-center"]}>
                            Excluir é permanente e só funciona em quadras sem reservas. Com histórico, desative.
                        </div>
                    </>
                )}
            </div>

            {editing && (
                <>
                    <ConfirmModal
                        open={confirmDelete}
                        icon={<Trash2 width={24} height={24} />}
                        title="Excluir quadra?"
                        message={`"${editing.name}" será removida permanentemente. Essa ação não pode ser desfeita.`}
                        confirmLabel="Excluir"
                        cancelLabel="Cancelar"
                        danger
                        onCancel={() => setConfirmDelete(false)}
                        onConfirm={() => remove(false)}
                    />
                    <ConfirmModal
                        open={confirmForce}
                        icon={<Trash2 width={24} height={24} />}
                        title="Excluir com as reservas?"
                        message={`"${editing.name}" tem reservas no histórico. Excluir permanentemente remove a quadra E todas as reservas/grupos/avaliações dela. Não dá pra desfazer — se quiser preservar o histórico, cancele e use Desativar.`}
                        confirmLabel="Excluir tudo"
                        cancelLabel="Cancelar"
                        danger
                        onCancel={() => setConfirmForce(false)}
                        onConfirm={() => remove(true)}
                    />
                </>
            )}
        </div>
    );
}

export default CourtsTab;
