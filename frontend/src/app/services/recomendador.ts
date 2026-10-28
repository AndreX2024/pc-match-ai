import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  UsuarioReq,
  RespuestaRecomendacion
} from '../models/recomendacion';

import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class RecomendadorService {

  private http = inject(HttpClient);

  recomendar(
    datos: UsuarioReq
  ): Observable<RespuestaRecomendacion> {

    return this.http.post<RespuestaRecomendacion>(
      `${environment.apiUrl}/recomendar`,
      datos
    );
  }
}