import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { UsuarioReq, RespuestaRecomendacion } from '../models/recomendacion';

@Injectable({ providedIn: 'root' })
export class RecomendadorService {
  private http = inject(HttpClient);

  recomendar(datos: UsuarioReq): Observable<RespuestaRecomendacion> {
    return this.http.post<RespuestaRecomendacion>('/api/recomendar', datos);
  }
}