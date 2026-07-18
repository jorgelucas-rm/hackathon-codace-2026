// Helpers de data/preço do painel da empresa — sem dependências externas.
// Datas sempre em horário local (nada de toISOString, que desloca o fuso).

export const HOURS = [
    "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00",
    "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00",
];

export const WEEK_SHORT = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];

// Códigos usados em Company.opening_hours (backend: _WEEKDAY_CODES, 0=segunda)
export const DAY_CODES = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"];
export const DAY_NAMES: Record<string, string> = {
    seg: "Segunda", ter: "Terça", qua: "Quarta", qui: "Quinta",
    sex: "Sexta", sab: "Sábado", dom: "Domingo",
};

function pad(n: number): string {
    return String(n).padStart(2, "0");
}

export function isoDate(d: Date): string {
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export interface DateChip {
    iso: string;
    week: string;
    day: string;
}

/** 7 dias a partir de hoje, para os chips da agenda. */
export function next7Days(): DateChip[] {
    const chips: DateChip[] = [];
    const today = new Date();
    for (let i = 0; i < 7; i++) {
        const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() + i);
        chips.push({ iso: isoDate(d), week: WEEK_SHORT[d.getDay()], day: pad(d.getDate()) });
    }
    return chips;
}

/** "sáb., 18 de jul." a partir de "2026-07-18". */
export function dateLabel(iso: string): string {
    const d = new Date(`${iso}T00:00:00`);
    return d.toLocaleDateString("pt-BR", { weekday: "short", day: "numeric", month: "short" });
}

/** "sábado, 18 de jul." (longo, usado no relatório). */
export function dateLabelLong(iso: string): string {
    const d = new Date(`${iso}T00:00:00`);
    return d.toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "short" });
}

/** "80,00" / "80.00" / "R$ 80" -> 8000 centavos. null se inválido. */
export function parsePriceToCents(value: string): number | null {
    const cleaned = value.replace(/[^\d.,]/g, "").replace(/\./g, "").replace(",", ".");
    if (!cleaned) return null;
    const parsed = parseFloat(cleaned);
    if (Number.isNaN(parsed) || parsed < 0) return null;
    return Math.round(parsed * 100);
}

/** 8000 -> "80,00" (para preencher o input de edição). */
export function centsToReaisInput(cents: number): string {
    return (cents / 100).toFixed(2).replace(".", ",");
}

export function isValidHHMM(value: string): boolean {
    return /^([01]\d|2[0-3]):[0-5]\d$/.test(value);
}

/** "19:00" -> "20:00" */
export function nextHour(h: string): string {
    const n = parseInt(h, 10) + 1;
    return `${pad(Math.min(n, 23))}:00`;
}

// ---------------------------------------------------------------------------
// Fotos: o backend guarda cada foto como uma data URL base64 no campo `photos`
// (limite ~700.000 chars). Redimensionamos no cliente para no máx. 800px de
// largura e exportamos JPEG, baixando a qualidade até caber no limite.
// ---------------------------------------------------------------------------

export const MAX_PHOTO_CHARS = 700_000;
const MAX_PHOTO_WIDTH = 800;

/** Lê um arquivo de imagem, redimensiona para no máx. 800px e devolve uma
 *  data URL JPEG dentro do limite do backend. Rejeita se não for imagem. */
export function fileToResizedDataUrl(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        if (!file.type.startsWith("image/")) {
            reject(new Error("Selecione um arquivo de imagem."));
            return;
        }
        const reader = new FileReader();
        reader.onerror = () => reject(new Error("Não foi possível ler o arquivo."));
        reader.onload = () => {
            const img = new Image();
            img.onerror = () => reject(new Error("Imagem inválida."));
            img.onload = () => {
                const scale = Math.min(1, MAX_PHOTO_WIDTH / img.width);
                const canvas = document.createElement("canvas");
                canvas.width = Math.round(img.width * scale);
                canvas.height = Math.round(img.height * scale);
                const ctx = canvas.getContext("2d");
                if (!ctx) {
                    reject(new Error("Falha ao processar a imagem."));
                    return;
                }
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                let quality = 0.85;
                let dataUrl = canvas.toDataURL("image/jpeg", quality);
                while (dataUrl.length > MAX_PHOTO_CHARS && quality > 0.3) {
                    quality -= 0.15;
                    dataUrl = canvas.toDataURL("image/jpeg", quality);
                }
                if (dataUrl.length > MAX_PHOTO_CHARS) {
                    reject(new Error("Imagem muito grande mesmo após compressão — use outra."));
                    return;
                }
                resolve(dataUrl);
            };
            img.src = reader.result as string;
        };
        reader.readAsDataURL(file);
    });
}
