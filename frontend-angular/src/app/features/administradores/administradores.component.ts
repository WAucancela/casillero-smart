import { Component, OnInit } from '@angular/core';
import { NgIf } from '@angular/common';
import { ApiService } from '../../core/api/api.service';

@Component({
  selector: 'app-administradores',
  standalone: true,
  imports: [NgIf],
  templateUrl: './administradores.component.html',
})
export class AdministradoresComponent implements OnInit {

  loading = true;
  error   = '';
  data: any[] = [];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading = true;
    this.error   = '';
  }
}
