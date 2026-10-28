import { TestBed } from '@angular/core/testing';
import { Recomendador } from './recomendador';

describe('Recomendador', () => {
  let service: Recomendador;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Recomendador);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
