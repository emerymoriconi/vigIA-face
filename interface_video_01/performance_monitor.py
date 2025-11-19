import time
import psutil

class PerformanceMonitor:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.metrics_history = []

    def start(self):
        """Inicia a medição de tempo."""
        self.start_time = time.perf_counter()

    def stop_and_record(self):
        """Finaliza a medição, calcula as métricas e as armazena."""
        self.end_time = time.perf_counter()
        
        if self.start_time and self.end_time:
            processing_time = (self.end_time - self.start_time) * 1000
            self.metrics_history.append({
                "processing_time_ms": processing_time,
                "cpu_percent": psutil.cpu_percent()
            })
        
        # Reseta os tempos para a próxima medição
        self.start_time = None
        self.end_time = None
    
    def get_summary(self):
        """Calcula a média das métricas registradas."""
        if not self.metrics_history:
            return None
            
        total_time = sum(m['processing_time_ms'] for m in self.metrics_history)
        total_cpu = sum(m['cpu_percent'] for m in self.metrics_history)
        
        num_frames = len(self.metrics_history)
        
        return {
            "avg_processing_time_ms": total_time / num_frames,
            "avg_cpu_percent": total_cpu / num_frames,
            "total_frames": num_frames
        }
        
    def save_to_file(self, algorithm_name, settings):
        """Salva o resumo em um arquivo de texto."""
        summary = self.get_summary()
        if not summary:
            return

        filename = "performance_log.txt"
        with open(filename, "a") as f: # Abre em modo 'append' para não sobrescrever
            f.write("--- Relatório de Desempenho ---\n")
            f.write(f"Algoritmo: {algorithm_name}\n")
            f.write(f"Resolução: {settings['width']}x{settings['height']}\n")
            f.write(f"FPS Alvo: {settings['desired_fps']}\n")
            f.write(f"Frames Processados: {summary['total_frames']}\n")
            f.write(f"Tempo Médio de Processamento: {summary['avg_processing_time_ms']:.2f} ms\n")
            f.write(f"Uso Médio da CPU: {summary['avg_cpu_percent']:.2f} %\n")
            f.write("-" * 30 + "\n\n")