import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ImagePlus, Loader2, LogOut, X } from "lucide-react";
import { OpeningHour } from "../../../services/companies.service";
import { CompanyMeUpdatePayload, PanelCompany } from "../../../services/companyPanel.service";
import { useAuth } from "../../../contexts/AuthContext";
import { ConfirmModal } from "../../../components/ConfirmModal/ConfirmModal";
import { useMyCompany, useUpdateMyCompany } from "../hooks/useCompanyPanel";
import { DAY_CODES, DAY_NAMES, fileToResizedDataUrl } from "../panelUtils";
import styles from "../CompanyPanel.module.scss";

interface DayForm {
    dia: string;
    ab: string;
    fe: string;
    fechado: boolean;
}

interface ProfileForm {
    description: string;
    phone: string;
    photos: string[];
    amenities: string[];
    street: string;
    number: string;
    neighborhood: string;
    zipCode: string;
    city: string;
    state: string;
    latitude: string;
    longitude: string;
    days: DayForm[];
}

function buildDays(openingHours: OpeningHour[]): DayForm[] {
    return DAY_CODES.map((dia) => {
        const found = openingHours.find((oh) => oh.dia_semana === dia);
        return {
            dia,
            ab: found?.abertura ?? "08:00",
            fe: found?.fechamento ?? "22:00",
            fechado: found ? found.fechado : true,
        };
    });
}

function buildForm(company: PanelCompany): ProfileForm {
    return {
        description: company.description ?? "",
        phone: company.phone ?? "",
        photos: company.photos ?? [],
        amenities: company.amenities ?? [],
        street: company.street ?? "",
        number: company.number ?? "",
        neighborhood: company.neighborhood ?? "",
        zipCode: company.zip_code ?? "",
        city: company.city ?? "",
        state: company.state ?? "",
        latitude: company.latitude !== null && company.latitude !== undefined ? String(company.latitude) : "",
        longitude: company.longitude !== null && company.longitude !== undefined ? String(company.longitude) : "",
        days: buildDays(company.opening_hours ?? []),
    };
}

export function ProfileTab() {
    const navigate = useNavigate();
    const { logout } = useAuth();
    const { data: company, isLoading, isError } = useMyCompany();
    const mutation = useUpdateMyCompany();

    const [form, setForm] = useState<ProfileForm | null>(null);
    const [newAmenity, setNewAmenity] = useState("");
    const [error, setError] = useState("");
    const [saved, setSaved] = useState(false);
    const [showLogoutModal, setShowLogoutModal] = useState(false);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Hidrata o formulário quando a empresa chega (uma vez só — edições do
    // usuário não são sobrescritas por refetches).
    useEffect(() => {
        if (company && !form) setForm(buildForm(company));
    }, [company, form]);

    if (isLoading || (!form && !isError)) {
        return <div className={styles["state-msg"]}><Loader2 width={18} height={18} /> Carregando perfil...</div>;
    }
    if (isError || !form) {
        return <div className={`${styles["state-msg"]} ${styles["state-error"]}`}>Erro ao carregar o perfil da arena.</div>;
    }

    const set = (patch: Partial<ProfileForm>) => setForm({ ...form, ...patch });

    const addAmenity = () => {
        const value = newAmenity.trim().toLowerCase();
        if (!value || form.amenities.includes(value)) return;
        set({ amenities: [...form.amenities, value] });
        setNewAmenity("");
    };

    const removeAmenity = (index: number) => {
        set({ amenities: form.amenities.filter((_, i) => i !== index) });
    };

    // Fotos: persiste na hora (o usuário vê a foto assim que sobe, sem precisar
    // clicar em "Salvar alterações"). Só o campo `photos` vai no PATCH.
    const persistPhotos = (photos: string[]) => {
        set({ photos });
        mutation.mutate(
            { photos },
            { onError: (e: Error) => setError(e.message) }
        );
    };

    const onPickFiles = async (fileList: FileList | null) => {
        if (!fileList || fileList.length === 0) return;
        setError("");
        setUploading(true);
        try {
            const encoded: string[] = [];
            for (const file of Array.from(fileList)) {
                encoded.push(await fileToResizedDataUrl(file));
            }
            persistPhotos([...form.photos, ...encoded]);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Falha ao enviar a imagem.");
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    const removePhoto = (index: number) => {
        persistPhotos(form.photos.filter((_, i) => i !== index));
    };

    const toggleDay = (index: number) => {
        set({ days: form.days.map((d, i) => (i === index ? { ...d, fechado: !d.fechado } : d)) });
    };

    const setDayTime = (index: number, field: "ab" | "fe", value: string) => {
        set({ days: form.days.map((d, i) => (i === index ? { ...d, [field]: value } : d)) });
    };

    const save = () => {
        const lat = form.latitude.trim() ? Number(form.latitude.replace(",", ".")) : null;
        const lng = form.longitude.trim() ? Number(form.longitude.replace(",", ".")) : null;
        if ((lat !== null && Number.isNaN(lat)) || (lng !== null && Number.isNaN(lng))) {
            setError("Latitude/longitude inválidas — use números (ex.: -3.7261).");
            return;
        }
        const badDay = form.days.find(
            (d) => !d.fechado && (!/^\d{2}:\d{2}$/.test(d.ab) || !/^\d{2}:\d{2}$/.test(d.fe))
        );
        if (badDay) {
            setError(`Horário inválido em ${DAY_NAMES[badDay.dia]} — use o formato HH:MM.`);
            return;
        }
        setError("");

        const dto: CompanyMeUpdatePayload = {
            description: form.description.trim() || null,
            phone: form.phone.trim() || null,
            photos: form.photos,
            latitude: lat,
            longitude: lng,
            amenities: form.amenities,
            opening_hours: form.days.map((d) => ({
                dia_semana: d.dia,
                abertura: d.fechado ? null : d.ab,
                fechamento: d.fechado ? null : d.fe,
                fechado: d.fechado,
            })),
        };
        // Campos de endereço têm min_length no backend — só envia preenchidos.
        if (form.street.trim()) dto.street = form.street.trim();
        if (form.number.trim()) dto.number = form.number.trim();
        if (form.neighborhood.trim()) dto.neighborhood = form.neighborhood.trim();
        if (form.zipCode.trim()) dto.zip_code = form.zipCode.trim();
        if (form.city.trim()) dto.city = form.city.trim();
        if (form.state.trim().length === 2) dto.state = form.state.trim().toUpperCase();

        mutation.mutate(dto, {
            onSuccess: () => {
                setSaved(true);
                setTimeout(() => setSaved(false), 2500);
            },
            onError: (e: Error) => setError(e.message),
        });
    };

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    return (
        <>
            <div className={styles["eyebrow"]}>Sua arena</div>
            <div className={styles["tab-title"]}>Perfil da empresa</div>

            <div className={styles["profile-grid"]}>
                <div className={styles["profile-col"]}>
                    {/* ---------- Fotos da arena ---------- */}
                    <div className={styles["panel-card"]}>
                        <div className={styles["card-title"]}>Fotos da arena</div>
                        <div className={styles["photo-grid"]}>
                            {form.photos.map((photo, i) => (
                                <div key={i} className={styles["photo-thumb"]}>
                                    <img src={photo} alt={`Foto da arena ${i + 1}`} />
                                    {i === 0 && <span className={styles["photo-cover-tag"]}>Capa</span>}
                                    <button
                                        type="button"
                                        className={styles["photo-remove"]}
                                        onClick={() => removePhoto(i)}
                                        aria-label={`Remover foto ${i + 1}`}
                                        disabled={uploading}
                                    >
                                        <X width={14} height={14} />
                                    </button>
                                </div>
                            ))}
                            <button
                                type="button"
                                className={styles["photo-add"]}
                                onClick={() => fileInputRef.current?.click()}
                                disabled={uploading}
                            >
                                {uploading
                                    ? <Loader2 width={20} height={20} className={styles["spin"]} />
                                    : <ImagePlus width={20} height={20} />}
                                <span>{uploading ? "Enviando..." : "Adicionar"}</span>
                            </button>
                        </div>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            multiple
                            hidden
                            onChange={(e) => onPickFiles(e.target.files)}
                        />
                        <div className={styles["tip"]}>
                            A primeira foto é a capa que aparece para os jogadores. Redimensionamos para
                            800px antes de enviar. A foto aparece assim que o upload termina.
                        </div>
                    </div>

                    {/* ---------- Sobre a arena ---------- */}
                    <div className={styles["panel-card"]}>
                        <div className={styles["card-title"]}>Sobre a arena</div>

                        <label className={styles["field-label"]}>Descrição</label>
                        <textarea
                            rows={3}
                            className={`${styles["text-input"]} ${styles["textarea"]}`}
                            value={form.description}
                            onChange={(e) => set({ description: e.target.value })}
                        />

                        <label className={`${styles["field-label"]} ${styles["field-gap"]}`}>Telefone</label>
                        <input
                            className={styles["text-input"]}
                            placeholder="(85) 3222-1000"
                            value={form.phone}
                            onChange={(e) => set({ phone: e.target.value })}
                        />

                        <div className={styles["card-title"]} style={{ margin: "18px 0 12px" }}>Comodidades</div>
                        <div className={styles["amenities"]}>
                            {form.amenities.map((amenity, i) => (
                                <span key={`${amenity}-${i}`} className={styles["amenity-chip"]}>
                                    {amenity}
                                    <button onClick={() => removeAmenity(i)} aria-label={`Remover ${amenity}`}>×</button>
                                </span>
                            ))}
                        </div>
                        <div className={styles["amenity-add"]}>
                            <input
                                placeholder="ex.: churrasqueira"
                                value={newAmenity}
                                onChange={(e) => setNewAmenity(e.target.value)}
                                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addAmenity(); } }}
                            />
                            <button onClick={addAmenity}>Adicionar</button>
                        </div>
                        <div className={styles["tip"]}>
                            Dica: "estacionamento", "wifi", "bar/lanchonete" e "vestiario" ganham ícone automático no
                            app do jogador.
                        </div>
                    </div>

                    {/* ---------- Endereço ---------- */}
                    <div className={styles["panel-card"]}>
                        <div className={styles["card-title"]}>Endereço</div>
                        <div className={styles["addr-grid"]}>
                            <input className={styles["text-input"]} placeholder="Rua" value={form.street} onChange={(e) => set({ street: e.target.value })} />
                            <input className={styles["text-input"]} placeholder="Número" value={form.number} onChange={(e) => set({ number: e.target.value })} />
                            <input className={styles["text-input"]} placeholder="Bairro" value={form.neighborhood} onChange={(e) => set({ neighborhood: e.target.value })} />
                            <input className={styles["text-input"]} placeholder="CEP" value={form.zipCode} onChange={(e) => set({ zipCode: e.target.value })} />
                            <input className={styles["text-input"]} placeholder="Cidade" value={form.city} onChange={(e) => set({ city: e.target.value })} />
                            <input className={styles["text-input"]} placeholder="UF" value={form.state} onChange={(e) => set({ state: e.target.value.toUpperCase().slice(0, 2) })} />
                        </div>
                        <div className={styles["latlng-grid"]}>
                            <div>
                                <label className={styles["field-label"]}>Latitude</label>
                                <input className={styles["text-input"]} placeholder="-3.7261" value={form.latitude} onChange={(e) => set({ latitude: e.target.value })} />
                            </div>
                            <div>
                                <label className={styles["field-label"]}>Longitude</label>
                                <input className={styles["text-input"]} placeholder="-38.4977" value={form.longitude} onChange={(e) => set({ longitude: e.target.value })} />
                            </div>
                        </div>
                        <div className={styles["tip"]}>
                            Sem latitude/longitude a arena não aparece na busca por distância dos jogadores.
                        </div>
                    </div>
                </div>

                <div className={styles["profile-col"]}>
                    {/* ---------- Horário de funcionamento ---------- */}
                    <div className={styles["panel-card"]}>
                        <div className={styles["card-title"]} style={{ marginBottom: 4 }}>Horário de funcionamento</div>
                        <div className={styles["tip"]} style={{ margin: "0 0 14px" }}>
                            Dias fechados não abrem horários para reserva no app.
                        </div>
                        <div className={styles["days-col"]}>
                            {form.days.map((day, i) => (
                                <div key={day.dia} className={styles["day-row"]}>
                                    <div className={styles["day-name"]}>{DAY_NAMES[day.dia]}</div>
                                    <button
                                        className={`${styles["day-toggle"]} ${day.fechado ? styles["day-closed"] : styles["day-open"]}`}
                                        onClick={() => toggleDay(i)}
                                    >
                                        {day.fechado ? "Fechado" : "Aberto"}
                                    </button>
                                    <div className={`${styles["day-times"]} ${day.fechado ? styles["day-times-off"] : ""}`}>
                                        <input
                                            className={styles["time-input"]}
                                            value={day.ab}
                                            onChange={(e) => setDayTime(i, "ab", e.target.value)}
                                        />
                                        <span>–</span>
                                        <input
                                            className={styles["time-input"]}
                                            value={day.fe}
                                            onChange={(e) => setDayTime(i, "fe", e.target.value)}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {error && <p className={styles["form-error"]} style={{ margin: 0 }}>{error}</p>}

                    <button className={styles["save-btn"]} onClick={save} disabled={mutation.isPending}>
                        {mutation.isPending ? "Salvando..." : "Salvar alterações"}
                    </button>
                    {saved && <div className={styles["saved-note"]}>✓ Alterações salvas</div>}

                    <div className={styles["logout-wrap"]}>
                        <button className={styles["logout-btn"]} onClick={() => setShowLogoutModal(true)}>
                            <LogOut width={18} height={18} /> Sair da conta
                        </button>
                    </div>
                </div>
            </div>

            <ConfirmModal
                open={showLogoutModal}
                icon={<LogOut width={24} height={24} />}
                title="Sair da conta?"
                message="Você precisará entrar novamente para acessar o painel da sua arena."
                confirmLabel="Confirmar saída"
                cancelLabel="Cancelar"
                danger
                onCancel={() => setShowLogoutModal(false)}
                onConfirm={() => { setShowLogoutModal(false); handleLogout(); }}
            />
        </>
    );
}

export default ProfileTab;
