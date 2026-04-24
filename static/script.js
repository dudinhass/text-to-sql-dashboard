document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const resultsArea = document.getElementById('results-area');
    const loadingState = document.getElementById('loading-state');
    const resultsContent = document.getElementById('results-content');
    const loadingText = document.getElementById('loading-text');
    const sqlCode = document.getElementById('sql-code');
    const submitBtn = chatForm.querySelector('.submit-btn');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const query = chatInput.value.trim();
        if (!query) return;

        // Visual feedback
        const originalBtnHtml = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="ph ph-spinner ph-spin"></i><span>Analisando...</span>';
        submitBtn.disabled = true;

        // Show loading state
        resultsArea.classList.remove('hidden');
        if (loadingState) loadingState.classList.remove('hidden');
        if (resultsContent) resultsContent.classList.add('hidden');

        const loadingPhrases = [
            "Traduzindo para SQL...",
            "Consultando banco de dados...",
            "Analisando resultados...",
            "Gerando insights...",
            "Montando gráficos..."
        ];
        let phraseIndex = 0;
        if(loadingText) loadingText.textContent = loadingPhrases[phraseIndex];
        
        let phraseInterval = setInterval(() => {
            phraseIndex = (phraseIndex + 1) % loadingPhrases.length;
            if(loadingText) loadingText.textContent = loadingPhrases[phraseIndex];
        }, 1500);

        try {
            console.log("Enviando query para o servidor:", query);
            
            // Fazendo fetch para a Fase 2 (endpoint /chat)
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: query })
            });

            if (!response.ok) {
                let errDetail = `Erro HTTP ${response.status}`;
                try {
                    const errJson = await response.json();
                    errDetail = errJson.detail || errDetail;
                } catch (_) {}
                throw new Error(errDetail);
            }

            const result = await response.json();
            console.log("Resposta recebida do servidor:", result);

            // 1. Esconde loading e mostra a área de resultados IMEDIATAMENTE
            if(loadingState) loadingState.classList.add('hidden');
            if(resultsContent) resultsContent.classList.remove('hidden');

            // 2. Injeta a resposta e o SQL na UI
            sqlCode.textContent = result.sql;
            
            const analysisAnswer = document.getElementById('analysis-answer');
            if (analysisAnswer) {
                analysisAnswer.innerHTML = marked.parse(result.answer || "Nenhuma resposta textual retornada.");
            }
            
            // 3. Renderiza o gráfico de forma assíncrona (não bloqueia a exibição da resposta)
            const chartContainer = document.querySelector('.chart-container');
            const ctx = document.getElementById('resultsChart');
            if(ctx && result.chart_data) {
                // Só mostra o gráfico se o backend enviar dados reais
                if(chartContainer) chartContainer.style.display = 'block';
                if(window.resultsChartInstance) {
                    window.resultsChartInstance.destroy();
                }
                requestAnimationFrame(() => {
                    window.resultsChartInstance = new Chart(ctx, {
                        type: 'line',
                        data: result.chart_data,
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: true, labels: { color: '#667085' } } },
                            scales: {
                                y: { grid: { color: 'rgba(234, 236, 240, 0.5)' }, ticks: { color: '#667085' } },
                                x: { grid: { display: false }, ticks: { color: '#667085' } }
                            }
                        }
                    });
                });
            } else {
                // Sem dados de gráfico: esconde o container para não mostrar área em branco
                if(chartContainer) chartContainer.style.display = 'none';
            }
            
        } catch (error) {
            console.error("Erro ao comunicar com a API:", error);
            
            // Tenta extrair a mensagem de erro do backend
            let errorMsg = error.message;
            try {
                // Se for um erro HTTP com corpo JSON
                if (error.body) {
                    const errBody = JSON.parse(error.body);
                    errorMsg = errBody.detail || errorMsg;
                }
            } catch (_) {}

            if(loadingState) loadingState.classList.add('hidden');
            if(resultsContent) resultsContent.classList.remove('hidden');
            
            const analysisAnswer = document.getElementById('analysis-answer');
            if (analysisAnswer) {
                analysisAnswer.innerHTML = `<div style="color:#F97066; padding: 12px; background: rgba(249,112,102,0.08); border-left: 3px solid #F97066; border-radius: 6px;">
                    <strong>❌ Erro na análise</strong><br/>
                    <span style="font-size:0.9em; opacity:0.85;">${errorMsg}</span>
                </div>`;
            }
            if(sqlCode) sqlCode.textContent = "-- " + errorMsg;
        } finally {
            if(phraseInterval) clearInterval(phraseInterval);
            // Restaura o botão
            submitBtn.innerHTML = originalBtnHtml;
            submitBtn.disabled = false;
        }
    });

    // Copy SQL button functionality
    const copySqlBtn = document.getElementById('copy-sql-btn');
    if (copySqlBtn) {
        copySqlBtn.addEventListener('click', () => {
            if(sqlCode && sqlCode.textContent) {
                navigator.clipboard.writeText(sqlCode.textContent)
                    .then(() => {
                        const originalHtml = copySqlBtn.innerHTML;
                        copySqlBtn.innerHTML = '<i class="ph ph-check" style="color: #6CE9A6"></i> Copiado';
                        setTimeout(() => copySqlBtn.innerHTML = originalHtml, 2000);
                    });
            }
        });
    }

    // Keep old copy button functionality if it exists
    const copyBtn = document.querySelector('.copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(sqlCode.textContent)
                .then(() => {
                    const originalIcon = copyBtn.innerHTML;
                    copyBtn.innerHTML = '<i class="ph ph-check" style="color: #6CE9A6"></i>';
                    setTimeout(() => copyBtn.innerHTML = originalIcon, 2000);
                });
        });
    }

    // Suggestion Chips functionality
    const chips = document.querySelectorAll('.chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            chatInput.value = chip.textContent;
            // Aciona o submit automaticamente
            submitBtn.click();
        });
    });
});
