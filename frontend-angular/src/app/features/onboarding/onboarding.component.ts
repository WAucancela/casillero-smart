import { Component, OnInit } from '@angular/core';
import { NgIf } from '@angular/common';
import { ApiService } from '../../core/api/api.service';

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [NgIf],
  templateUrl: './onboarding.component.html',
})
export class OnboardingComponent implements OnInit {

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
