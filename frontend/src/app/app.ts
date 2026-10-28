import { Component, signal } from '@angular/core';
import { Recomendador } from './recomendador/recomendador';

@Component({
  imports: [Recomendador],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected readonly title = signal('frontend');
}
