import { useMemo, useState } from "react";
import { Loader2 } from "lucide-react";
import { formatHHMM, formatPriceCents } from "../../../services/companyPanel.service";
import { useMyReport } from "../hooks/useCompanyPanel";
import { HOURS, dateLabelLong, isoDate } from "../panelUtils";
import styles from "../CompanyPanel.module.scss";

const PERIODS = ["Este mês", "Últimos 30 dias", "Este ano"];

function periodRange(period: number): { from: string; to: string } {
    const today = new Date();
    const to = isoDate(today);
    if (period === 0) {
        return { from: isoDate(new Date(today.getFullYear(), today.getMonth(), 1)), to };
    }
    if (period === 1) {
        return { from: isoDate(new Date(today.getFullYear(), today.getMonth(), today.getDate() - 29)), to };
    }
    return { from: isoDate(new Date(today.getFullYear(), 0, 1)), to };
}

export function ReportTab() {
    const [period, setPeriod] = useState(0);
    const { from, to } = useMemo(() => periodRange(period), [period]);
    const { data: report, isLoading, isError } = useMyReport(from, to);

    const occupancyPct = report ? Math.round(report.occupancy_rate * 100) : 0;
    const peakHour = report?.peak_hour ? formatHHMM(report.peak_hour) : null;

    return (
        <>
            <div className={styles["tab-head"]}>
                <div>
                    <div className={styles["eyebrow"]}>Desempenho</div>
                    <div className={styles["tab-title"]}>Relatório</div>
                </div>
                <div className={styles["period-chips"]}>
                    {PERIODS.map((label, i) => (
                        <button
                            key={label}
                            onClick={() => setPeriod(i)}
                            className={`${styles["period-chip"]} ${i === period ? styles["period-chip-active"] : ""}`}
                        >
                            {label}
                        </button>
                    ))}
                </div>
            </div>

            {isLoading && (
                <div className={styles["state-msg"]}><Loader2 width={18} height={18} /> Carregando relatório...</div>
            )}
            {isError && !isLoading && (
                <div className={`${styles["state-msg"]} ${styles["state-error"]}`}>Erro ao carregar o relatório. Tente novamente.</div>
            )}

            {report && (
                <>
                    <div className={styles["stats-grid"]}>
                        <div className={styles["panel-card"]}>
                            <div className={styles["stat-label"]}>Receita confirmada</div>
                            <div className={`${styles["stat-value"]} ${styles["stat-teal"]}`}>
                                {formatPriceCents(report.confirmed_revenue)}
                            </div>
                            <div className={styles["stat-sub"]}>reservas confirmadas e concluídas</div>
                        </div>

                        <div className={styles["panel-card"]}>
                            <div className={styles["stat-label"]}>Ocupação</div>
                            <div className={styles["stat-value"]}>{occupancyPct}%</div>
                            <div className={styles["occ-bar"]}>
                                <div className={styles["occ-fill"]} style={{ width: `${Math.min(occupancyPct, 100)}%` }} />
                            </div>
                            <div className={styles["stat-sub"]} style={{ marginTop: 6 }}>
                                {report.occupied_slots} de {report.available_slots} horários
                            </div>
                        </div>

                        <div className={styles["panel-card"]}>
                            <div className={styles["stat-label"]}>Reservas</div>
                            <div className={styles["stat-value"]}>{report.total_bookings}</div>
                            <div className={styles["stat-sub"]}>no período selecionado</div>
                        </div>
                    </div>

                    <div className={styles["report-row"]}>
                        <div className={styles["panel-card"]}>
                            <div className={styles["stat-label"]}>Reservas por horário</div>
                            <div className={styles["bars"]}>
                                {HOURS.map((hour) => {
                                    const isPeak = peakHour === hour;
                                    return (
                                        <div key={hour} className={styles["bar-col"]}>
                                            <div
                                                className={`${styles["bar"]} ${isPeak ? styles["bar-peak"] : ""}`}
                                                style={{ height: isPeak ? 104 : 14 }}
                                            />
                                            <span>{parseInt(hour, 10)}</span>
                                        </div>
                                    );
                                })}
                            </div>
                            <div className={styles["stat-sub"]} style={{ marginTop: 10 }}>
                                {peakHour
                                    ? `Horário de pico do período em destaque (${peakHour}).`
                                    : "Sem reservas no período para destacar um horário de pico."}
                            </div>
                        </div>

                        <div className={`${styles["panel-card"]} ${styles["peak-card"]}`}>
                            <div>
                                <div className={styles["stat-label"]}>Dia de pico</div>
                                <div className={styles["peak-value"]}>
                                    {report.peak_day ? dateLabelLong(report.peak_day) : "—"}
                                </div>
                            </div>
                            <div>
                                <div className={styles["stat-label"]}>Horário de pico</div>
                                <div className={styles["peak-value"]}>{peakHour ?? "—"}</div>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </>
    );
}

export default ReportTab;
