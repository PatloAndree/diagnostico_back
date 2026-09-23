<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('pacientes', function (Blueprint $table) {
            $table->id();
            $table->foreignId('institucion_id')->nullable()->constrained('instituciones')->restrictOnDelete();
            $table->string('nombres');
            $table->string('apellidos');
            $table->string('documento', 30)->nullable()->unique();
            $table->date('fecha_nacimiento');
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('pacientes');
    }
};