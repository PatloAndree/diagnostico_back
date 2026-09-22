<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('diagnostico_detalles', function (Blueprint $table) {
            $table->id();
            $table->foreignId('diagnostico_test_id')->constrained('diagnostico_tests')->restrictOnDelete();
            $table->string('concepto');
            $table->text('respuesta')->nullable();
            $table->decimal('puntaje', 10, 2)->nullable();
            $table->decimal('puntaje_maximo', 10, 2)->nullable();
            $table->decimal('porcentaje', 5, 2)->nullable();
            $table->foreignId('nivel_id')->nullable()->constrained('niveles')->restrictOnDelete();
            $table->text('observaciones')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('diagnostico_detalles');
    }
};