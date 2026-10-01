<?php

namespace Tests\Feature;

use App\Models\Paciente;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Tests\TestCase;

class DiagnosticoMinimoTest extends TestCase
{
    use RefreshDatabase;

    public function test_entrega_el_formulario_minimo(): void
    {
        $response = $this->getJson('/api/diagnosticos/minimo/formulario');

        $response->assertOk()
            ->assertJsonPath('codigo', 'diagnostico-minimo')
            ->assertJsonCount(4, 'preguntas');
    }

    public function test_ejecuta_el_script_y_guarda_el_diagnostico(): void
    {
        $user = User::factory()->create();
        $paciente = Paciente::create([
            'nombres' => 'Ana',
            'apellidos' => 'Prueba',
            'fecha_nacimiento' => '2000-01-01',
        ]);
        Sanctum::actingAs($user);

        $response = $this->postJson('/api/diagnosticos/minimo', [
            'paciente_id' => $paciente->id,
            'respuestas' => [
                'animo' => 3,
                'sueno' => 2,
                'energia' => 4,
                'concentracion' => 1,
            ],
        ]);

        $response->assertCreated()
            ->assertJsonPath('estado', 'completado')
            ->assertJsonPath('tests.0.puntaje_total', 8)
            ->assertJsonPath('tests.0.detalles.0.respuesta', '3');

        $this->assertDatabaseHas('diagnostico', [
            'paciente_id' => $paciente->id,
            'user_id' => $user->id,
            'estado' => 'completado',
        ]);
        $this->assertDatabaseCount('diagnostico_detalles', 4);
    }

    public function test_lista_y_muestra_el_detalle_de_un_diagnostico(): void
    {
        $user = User::factory()->create();
        $paciente = Paciente::create([
            'nombres' => 'Luis',
            'apellidos' => 'Detalle',
            'fecha_nacimiento' => '1998-01-01',
        ]);
        Sanctum::actingAs($user);

        $creado = $this->postJson('/api/diagnosticos/minimo', [
            'paciente_id' => $paciente->id,
            'respuestas' => [
                'animo' => 3,
                'sueno' => 3,
                'energia' => 3,
                'concentracion' => 3,
            ],
        ])->assertCreated();

        $diagnosticoId = $creado->json('id');

        $this->getJson('/api/diagnosticos?paciente_id='.$paciente->id)
            ->assertOk()
            ->assertJsonCount(1)
            ->assertJsonPath('0.id', $diagnosticoId);

        $this->getJson('/api/diagnosticos/'.$diagnosticoId)
            ->assertOk()
            ->assertJsonPath('id', $diagnosticoId)
            ->assertJsonPath('paciente.id', $paciente->id)
            ->assertJsonPath('tests.0.test.nombre', 'Diagnóstico mínimo de prueba')
            ->assertJsonCount(4, 'tests.0.detalles');
    }
}
