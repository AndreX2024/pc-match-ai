import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { RecomendadorService } from '../services/recomendador';
import { Configuracion, UsuarioReq } from '../models/recomendacion';

@Component({
  selector: 'app-recomendador',
  imports: [ReactiveFormsModule],
  templateUrl: './recomendador.html',
  styleUrl: './recomendador.css',
})
export class Recomendador {
  private fb = inject(FormBuilder);
  private api = inject(RecomendadorService);

  cargando = signal(false);
  error = signal<string | null>(null);
  resultados = signal<Configuracion[]>([]);
  buscado = signal(false);

  partes: { key: keyof Configuracion; nombre: string; precio: keyof Configuracion }[] = [
    { key: 'CPU', nombre: 'CPU', precio: 'precio_cpu_cop' },
    { key: 'CPU Cooler', nombre: 'Cooler', precio: 'precio_cooler_cop' },
    { key: 'Motherboard', nombre: 'Placa base', precio: 'precio_motherboard_cop' },
    { key: 'Memory', nombre: 'RAM', precio: 'precio_memory_cop' },
    { key: 'Storage', nombre: 'Almacenamiento', precio: 'precio_storage_cop' },
    { key: 'Video Card', nombre: 'GPU', precio: 'precio_video_card_cop' },
    { key: 'Power Supply', nombre: 'Fuente', precio: 'precio_power_supply_cop' },
    { key: 'Case', nombre: 'Gabinete', precio: 'precio_case_cop' },
  ];

  form = this.fb.group({
    presupuesto: [5000000, [Validators.required, Validators.min(1)]],
    uso_principal: ['Gaming', Validators.required],
    uso_secundario: [''],
    resolucion: ['1440p', Validators.required],
    fps_objetivo: [144, [Validators.required, Validators.min(1)]],
    juego: [''],
    software: [''],
    preferencia_marca: [''],
    cantidad: [5, [Validators.min(1), Validators.max(10)]],
  });

  enviar() {
    if (this.form.invalid) return;
    const v = this.form.getRawValue();
    const datos: UsuarioReq = {
      presupuesto: Number(v.presupuesto),
      uso_principal: v.uso_principal!,
      uso_secundario: v.uso_secundario || null,
      resolucion: v.resolucion as UsuarioReq['resolucion'],
      fps_objetivo: Number(v.fps_objetivo),
      juego: v.juego || null,
      software: v.software || null,
      preferencia_marca: (v.preferencia_marca || null) as UsuarioReq['preferencia_marca'],
      cantidad: Number(v.cantidad),
    };

    this.cargando.set(true);
    this.error.set(null);
    this.resultados.set([]);

    this.api.recomendar(datos).subscribe({
      next: (r) => {
        this.resultados.set(r.configuraciones);
        this.buscado.set(true);
        this.cargando.set(false);
      },
      error: (e: HttpErrorResponse) => {
        const detalle = e.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo conectar con el servidor.');
        this.cargando.set(false);
      },
    });
  }

  claseCategoria(c: string) {
    return c.replace(/\s/g, '-');
  }

  valor(c: Configuracion, k: keyof Configuracion) {
    return c[k];
  }
}