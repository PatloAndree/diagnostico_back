<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('diagnostico_tests', function (Blueprint $table) {
            $table->id();
            $table->foreignId('diagnostico_id')->constrained('diagnostico')->restrictOnDelete();
            $table->foreignId('test_id')->constrained('tests')->restrictOnDelete();
            $table->dateTime('fecha')->nullable();
            $table->decimal('puntaje_total', 10, 2)->nullable();
            $table->decimal('puntaje_maximo', 10, 2)->nullable();
            $table->decimal('porcentaje', 5, 2)->nullable();
            $table->foreignId('nivel_id')->nullable()->constrained('niveles')->restrictOnDelete();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('diagnostico_tests');
    }
};