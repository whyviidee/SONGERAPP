// web/static/js/views/faq.js

const FAQ_SECTIONS = [
  {
    icon: "download",
    title: "Downloads & Formatos",
    items: [
      {
        q: "Que formatos de áudio estão disponíveis?",
        a: "SONGER suporta FLAC, MP3 320kbps, MP3 256kbps e MP3 128kbps. Podes mudar o formato em Settings. Para uso geral, MP3 320kbps é a escolha ideal — boa qualidade sem ficheiros enormes."
      },
      {
        q: "O FLAC do YouTube é lossless de verdade?",
        a: "Não. O YouTube distribui áudio em formato AAC ou Opus (geralmente 128–256kbps). Quando escolhes FLAC com fonte YouTube, o SONGER descarrega esse áudio e converte-o para o container FLAC via FFmpeg. O ficheiro fica maior mas a qualidade é a do YouTube — não recupera informação que o YouTube já descartou. Para FLAC verdadeiro (lossless de CD), precisas do Soulseek."
      },
      {
        q: "Então MP3 320 e FLAC do YouTube soam igual?",
        a: "Na prática, sim — o tecto de qualidade é o áudio do YouTube, não o formato do ficheiro. Para a maioria dos utilizadores é impossível distinguir. Se queres qualidade real, usa Soulseek para encontrar rips de CD verdadeiramente lossless."
      },
      {
        q: "Como funciona o modo Hybrid (Soulseek + YouTube)?",
        a: "O SONGER tenta primeiro encontrar a música no Soulseek — que tem uma vasta biblioteca de FLAC e MP3 de alta qualidade partilhados por utilizadores reais. Se não encontrar (ou o Soulseek estiver offline), usa o YouTube como fallback automático. É o modo recomendado se tiveres Soulseek configurado."
      },
      {
        q: "Onde ficam guardados os ficheiros?",
        a: "Na pasta que definiste em Settings → Download Path. Por defeito, os ficheiros são organizados por Artista/Álbum. Podes mudar a pasta em qualquer altura sem perder o que já foi descarregado."
      },
      {
        q: "Posso descarregar uma playlist inteira de uma vez?",
        a: "Sim. Vai a Playlists → abre a playlist → 'Download All'. Todas as faixas são adicionadas à fila e descarregadas em sequência. Podes também descarregar em ZIP (uma pasta comprimida com todas as faixas)."
      },
      {
        q: "O download falhou. O que posso fazer?",
        a: "Vai a Settings e verifica se tens um Download Path definido. Se estás a usar YouTube, verifica a ligação à internet. Se estás a usar Soulseek, confirma que o slskd está a correr. Podes tentar novamente clicando no botão de retry na fila."
      }
    ]
  },
  {
    icon: "music",
    title: "Spotify",
    items: [
      {
        q: "Porque é que preciso de credenciais Spotify?",
        a: "O SONGER usa a API oficial do Spotify para ler as tuas playlists, liked songs e metadados (nome, artista, álbum, capa). Não acede à tua conta para ouvir música — só lê informação. O Spotify disponibiliza esta API gratuitamente para uso pessoal."
      },
      {
        q: "A minha conta Spotify pode ser banida?",
        a: "É extremamente improvável. O SONGER usa apenas a API oficial de leitura (sem streaming, sem controlo de reprodução). O Spotify não tem forma de saber que estás a descarregar música a partir dos metadados que lês — são operações completamente separadas. Tens muito mais utilizadores a fazer web scraping agressivo sem qualquer consequência."
      },
      {
        q: "Funciona com conta Spotify gratuita?",
        a: "Sim. Todas as funcionalidades do SONGER — liked songs, playlists, pesquisa, metadados — funcionam com conta gratuita. O Premium não é necessário para nada no SONGER."
      },
      {
        q: "O SONGER acede à minha palavra-passe do Spotify?",
        a: "Não. A autenticação usa OAuth 2.0 — o protocolo padrão da indústria. O SONGER nunca vê a tua palavra-passe. Autenticas directamente nos servidores do Spotify, que devolvem um token de acesso limitado (só leitura de biblioteca)."
      },
      {
        q: "O que acontece quando o token do Spotify expira?",
        a: "O SONGER renova o token automaticamente em background usando o refresh token. Não precisas de fazer login novamente. Só precisas de re-autenticar se fizeres logout manual ou se apagares o ficheiro de token."
      }
    ]
  },
  {
    icon: "wifi",
    title: "Soulseek",
    items: [
      {
        q: "O que é o Soulseek?",
        a: "Soulseek é uma rede P2P (peer-to-peer) de partilha de música, activa desde 2000. É muito popular entre audiófilos por ter uma enorme biblioteca de FLAC lossless, vinis digitalizados e raridades impossíveis de encontrar noutros serviços. É o único caminho para FLAC verdadeiro no SONGER."
      },
      {
        q: "O Soulseek é obrigatório?",
        a: "Não. O SONGER funciona perfeitamente com só o YouTube. O Soulseek é opcional e adiciona acesso a qualidade superior (FLAC real) e a música difícil de encontrar no YouTube."
      },
      {
        q: "Como configuro o Soulseek?",
        a: "Precisas de: (1) criar uma conta gratuita em slsknet.org, (2) instalar o slskd (daemon Soulseek), (3) configurar em Settings. Vai a Settings → clica 'Configurar Soulseek' para um guia passo a passo dentro do SONGER."
      },
      {
        q: "Porque é que aparece 'Soulseek offline'?",
        a: "O slskd não está a correr ou não está configurado. O SONGER liga ao slskd via API local (porta 5030 por defeito). Confirma que o slskd está iniciado antes de abrir o SONGER. Se tens o hybrid activado, os downloads continuam via YouTube sem interrupção."
      },
      {
        q: "O meu IP fica exposto no Soulseek?",
        a: "Tecnicamente sim — como em qualquer rede P2P, o teu IP é visível para outros utilizadores Soulseek durante as transferências. Podes usar uma VPN para ocultar o IP se isso for uma preocupação. O Soulseek existe há mais de 20 anos com um historial de acção legal mínima contra utilizadores individuais."
      }
    ]
  },
  {
    icon: "shield",
    title: "Legal & Responsabilidade",
    items: [
      {
        q: "É legal descarregar música com o SONGER?",
        a: "Depende do país e do uso. Em muitos países, descarregar música protegida por direitos de autor para uso pessoal está numa zona cinzenta legal. O SONGER é uma ferramenta — a responsabilidade legal pelo uso é inteiramente do utilizador. Verifica as leis de direitos de autor do teu país antes de utilizar."
      },
      {
        q: "O SONGER pode ser responsabilizado pelo que descarrego?",
        a: "Não. O SONGER é software open source que automatiza acções que qualquer utilizador poderia fazer manualmente. Os criadores do SONGER não têm qualquer responsabilidade pelo uso que fazes da ferramenta, tal como os criadores do yt-dlp, wget ou qualquer browser não são responsáveis pelo que descarregas com eles."
      },
      {
        q: "O SONGER guarda os meus dados?",
        a: "Todos os dados ficam no teu computador. O SONGER não tem servidores externos, não envia telemetria, não regista o que descarregas. O ficheiro de configuração fica em ~/.songer/config.json e o token Spotify em ~/.songer/.spotify_token.json — ambos locais, nunca partilhados."
      },
      {
        q: "O SONGER viola os Termos de Serviço do Spotify?",
        a: "O uso da API do Spotify para leitura pessoal de playlists/biblioteca está dentro dos termos para aplicações em 'Development Mode'. O SONGER não faz streaming não autorizado, não redistribui conteúdo Spotify, não usa a API para fins comerciais."
      },
      {
        q: "O que faço se receber um aviso legal?",
        a: "Para de usar o SONGER imediatamente para o conteúdo em questão e procura aconselhamento jurídico. Os criadores do SONGER não fornecem assistência legal e não têm qualquer responsabilidade por acções legais resultantes do uso da ferramenta."
      }
    ]
  },
  {
    icon: "wrench",
    title: "Problemas Comuns",
    items: [
      {
        q: "O download fica a 0% e não avança.",
        a: "Provável causa: sem ligação à internet, yt-dlp desactualizado, ou o YouTube bloqueou temporariamente o IP. Tenta novamente. Se persistir, reinicia o SONGER — o yt-dlp é actualizado automaticamente no arranque."
      },
      {
        q: "Erro 'ffmpeg not found' nos downloads.",
        a: "O SONGER inclui o ffmpeg automaticamente via imageio-ffmpeg. Se esse erro aparecer, vai a Settings e verifica o Download Path. Reiniciar o servidor (Ctrl+C e iniciar novamente) normalmente resolve."
      },
      {
        q: "As minhas playlists Spotify não aparecem.",
        a: "O token Spotify pode ter expirado ou corrompido. Vai à página principal do SONGER (localhost:8888), clica 'Desligar conta Spotify' e volta a autenticar. O processo demora menos de um minuto."
      },
      {
        q: "A fila de downloads está vazia mas tenho músicas para descarregar.",
        a: "Clica no item da fila para ver o estado. Músicas com erro aparecem com ícone vermelho — podes tentar novamente ou removê-las. Se a fila aparece completamente vazia após reiniciar, é normal — a fila não persiste entre sessões."
      },
      {
        q: "Como actualizo o SONGER?",
        a: "Para já, actualização é manual — substitui os ficheiros pela versão mais recente. Em versões futuras está planeado um sistema de actualização automática."
      }
    ]
  }
];

function renderFaq() {
  const content = document.getElementById("content");
  content.innerHTML = `
    <div class="view-header">
      <span class="view-title">Help & FAQ</span>
    </div>

    <div class="disclaimer-banner">
      <div class="disclaimer-icon"><i data-lucide="triangle-alert" width="16" height="16"></i></div>
      <div class="disclaimer-text">
        <strong>Aviso Legal</strong> — O SONGER é uma ferramenta pessoal de código aberto.
        O utilizador é inteiramente responsável pelo uso que faz do software e pelo cumprimento
        das leis de direitos de autor do seu país. Os criadores do SONGER não têm qualquer
        responsabilidade por acções legais decorrentes do uso desta ferramenta.
        <strong>Use de forma responsável.</strong>
      </div>
    </div>

    <div class="faq-list" id="faq-list">
      ${FAQ_SECTIONS.map((section, si) => `
        <div class="faq-section">
          <div class="faq-section-header">
            <i data-lucide="${section.icon}" width="16" height="16"></i>
            <span>${section.title}</span>
          </div>
          ${section.items.map((item, ii) => `
            <div class="faq-item" id="faq-${si}-${ii}">
              <div class="faq-question" onclick="toggleFaq('faq-${si}-${ii}')">
                <span>${item.q}</span>
                <i data-lucide="chevron-down" width="14" height="14" class="faq-chevron"></i>
              </div>
              <div class="faq-answer">${item.a}</div>
            </div>
          `).join("")}
        </div>
      `).join("")}
    </div>
  `;
  lucide.createIcons();
}

function toggleFaq(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const isOpen = el.classList.contains("open");
  // Close all
  document.querySelectorAll(".faq-item.open").forEach(i => i.classList.remove("open"));
  // Open this one if it wasn't open
  if (!isOpen) el.classList.add("open");
}
