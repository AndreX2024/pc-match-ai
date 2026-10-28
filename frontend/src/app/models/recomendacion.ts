export interface UsuarioReq {
  presupuesto: number;
  uso_principal: string;
  uso_secundario: string | null;
  resolucion: '1080p' | '1440p' | '4K';
  fps_objetivo: number;
  juego: string | null;
  software: string | null;
  preferencia_marca: 'AMD' | 'Intel' | 'NVIDIA' | null;
  cantidad: number;
}

export interface Configuracion {
  id_configuracion: string;
  CPU: string;
  'CPU Cooler': string;
  Motherboard: string;
  Memory: string;
  Storage: string;
  'Video Card': string;
  'Power Supply': string;
  Case: string;
  precio_total_cop: number;
  precio_total_formateado: string;
  precio_cpu_cop: string;
  precio_cooler_cop: string;
  precio_motherboard_cop: string;
  precio_memory_cop: string;
  precio_storage_cop: string;
  precio_video_card_cop: string;
  precio_power_supply_cop: string;
  precio_case_cop: string;
  categoria: 'No recomendado' | 'Aceptable' | 'Excelente' | 'Ideal';
  probabilidad_estimada_categoria_pct: number;
  compatibilidad: string;
}

export interface RespuestaRecomendacion {
  total: number;
  configuraciones: Configuracion[];
}
