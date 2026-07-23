(function(){
var AREAS_DATA=[
  {
    id:'dev', nome:'Desenvolvimento de Software', pct:35.7,
    descShort:'Concepção, construção e manutenção de aplicações e sistemas digitais. Do front-end ao back-end.',
    junior:22, pleno:73, lideranca:5,
    tipo:'esp',
    softSkills:[
      {t:'Comunicação',v:'33,6%'},{t:'Criatividade',v:'31,3%'},
      {t:'Organização',v:'23,9%'},{t:'Trabalho em equipe',v:'21,1%'}
    ],
    niveis:[
      {n:'Júnior 22%', pct:'22%', chips:[
        {t:'Javascript',c:'lang'},{t:'SQL',c:'lang'},{t:'Git',c:'tool'},{t:'HTML/CSS',c:'lang'},{t:'Comunicação',c:'soft'}
      ], diferencial:'Portfólio no GitHub com projetos reais'},
      {n:'Pleno/Sênior 73%', pct:'73%', chips:[
        {t:'React/Angular',c:'hard'},{t:'AWS',c:'hard'},{t:'Docker',c:'tool'},{t:'CI/CD',c:'hard'},{t:'Trabalho em equipe',c:'soft'}
      ], diferencial:'Feature entregue em produto real'},
      {n:'Liderança 5%', pct:'5%', chips:[
        {t:'Sistemas distribuídos',c:'hard'},{t:'Design patterns',c:'hard'},{t:'Comunicação',c:'soft'},{t:'Liderança',c:'soft'}
      ], diferencial:'Decisões técnicas que envelheceram bem'}
    ],
    fonte:'Inteli — Índice de Vagas (Web Scraping, 2025)'
  },
  {
    id:'infra', nome:'Infraestrutura e Suporte', pct:23.2,
    descShort:'Manter ambientes, redes, servidores e sistemas operacionais. Estabilidade e segurança da operação.',
    junior:43, pleno:50, lideranca:8,
    tipo:'entrada',
    softSkills:[
      {t:'Comunicação',v:'37,5%'},{t:'Organização',v:'26,0%'},
      {t:'Criatividade',v:'25,4%'},{t:'Resolução de problemas',v:'20,2%'}
    ],
    niveis:[
      {n:'Júnior 43%', pct:'43%', chips:[
        {t:'Windows',c:'hard'},{t:'Linux',c:'hard'},{t:'Redes',c:'hard'},{t:'Office 365',c:'tool'},{t:'Resolução de problemas',c:'soft'}
      ], diferencial:'Certificação CompTIA A+ ou ITIL'},
      {n:'Pleno/Sênior 50%', pct:'50%', chips:[
        {t:'AWS/Azure',c:'hard'},{t:'Terraform',c:'tool'},{t:'Docker',c:'tool'},{t:'Grafana',c:'tool'},{t:'Organização',c:'soft'}
      ], diferencial:'Participação em migração para cloud'},
      {n:'Liderança 8%', pct:'8%', chips:[
        {t:'Cloud multi-região',c:'hard'},{t:'FinOps',c:'hard'},{t:'SRE',c:'hard'},{t:'Liderança',c:'soft'}
      ], diferencial:'Uptime comprovado em sistemas críticos'}
    ],
    fonte:'Inteli — Índice de Vagas (Web Scraping, 2025)'
  },
  {
    id:'dados', nome:'Dados e Inteligência Artificial', pct:17.7,
    descShort:'Coleta, tratamento, modelagem e análise de dados para geração de insights e automação inteligente.',
    junior:18, pleno:76, lideranca:6,
    tipo:'esp',
    softSkills:[
      {t:'Comunicação',v:'39,8%'},{t:'Criatividade',v:'37,8%'},
      {t:'Pensamento analítico',v:'30,9%'},{t:'Organização',v:'28,0%'}
    ],
    niveis:[
      {n:'Júnior 18%', pct:'18%', chips:[
        {t:'Python',c:'lang'},{t:'SQL',c:'lang'},{t:'Power BI',c:'tool'},{t:'Git',c:'tool'},{t:'Pens. analítico',c:'soft'}
      ], diferencial:'Projeto publicado no GitHub ou Kaggle. Nota: 3,6% das vagas Pleno/Sênior exigem pós-graduação'},
      {n:'Pleno/Sênior 76%', pct:'76%', chips:[
        {t:'Python',c:'lang'},{t:'SQL',c:'lang'},{t:'AWS/Azure',c:'hard'},{t:'Spark',c:'hard'},{t:'Machine Learning',c:'hard'}
      ], diferencial:'Pipeline ou modelo em produção'},
      {n:'Liderança 6%', pct:'6%', chips:[
        {t:'Data Mesh',c:'hard'},{t:'MLOps',c:'hard'},{t:'Governança',c:'hard'},{t:'Liderança',c:'soft'}
      ], diferencial:'Arquitetura de dados construída e validada'}
    ],
    fonte:'Inteli — Índice de Vagas (Web Scraping, 2025)'
  },
  {
    id:'projetos', nome:'Projetos e Gerenciamento', pct:12.9,
    descShort:'Coordenação de equipes, prazos, escopo e recursos para entregas estratégicas. Maior % de liderança entre todas as áreas.',
    junior:24, pleno:54, lideranca:21,
    tipo:null,
    softSkills:[
      {t:'Comunicação',v:'42,5%'},{t:'Organização',v:'34,6%'},
      {t:'Criatividade',v:'33,2%'},{t:'Liderança',v:'19,9%'}
    ],
    niveis:[
      {n:'Júnior 24%', pct:'24%', chips:[
        {t:'Excel',c:'tool'},{t:'Jira',c:'tool'},{t:'Scrum',c:'hard'},{t:'Kanban',c:'hard'},{t:'Organização',c:'soft'}
      ], diferencial:'Ter liderado algo real — mesmo em contexto acadêmico'},
      {n:'Pleno/Sênior 54%', pct:'54%', chips:[
        {t:'Power BI',c:'tool'},{t:'SQL',c:'lang'},{t:'Met. Ágeis',c:'hard'},{t:'Comunicação',c:'soft'},{t:'Liderança',c:'soft'}
      ], diferencial:'Projetos entregues com impacto mensurável'},
      {n:'Liderança 21%', pct:'21%', chips:[
        {t:'OKRs',c:'hard'},{t:'Budget',c:'hard'},{t:'C-level',c:'soft'},{t:'Comunicação',c:'soft'}
      ], diferencial:'MBA ou pós + programas transformacionais. Nota: 9,3% das vagas de liderança exigem pós-graduação'}
    ],
    fonte:'Inteli — Índice de Vagas (Web Scraping, 2025)'
  },
  {
    id:'testes', nome:'Testes e Controle de Qualidade', pct:5.7,
    descShort:'Garantir qualidade, estabilidade e segurança de sistemas antes da entrega. Melhor custo-benefício de entrada em tech.',
    junior:26, pleno:69, lideranca:5,
    tipo:'entrada',
    softSkills:[
      {t:'Comunicação',v:'37,5%'},{t:'Organização',v:'26,0%'},
      {t:'Criatividade',v:'25,4%'},{t:'Resolução de problemas',v:'20,2%'}
    ],
    niveis:[
      {n:'Júnior 26%', pct:'26%', chips:[
        {t:'Selenium',c:'tool'},{t:'Cypress',c:'tool'},{t:'Postman',c:'tool'},{t:'Git',c:'tool'},{t:'Criatividade',c:'soft'}
      ], diferencial:'Qualquer automação de teste no portfólio'},
      {n:'Pleno/Sênior 69%', pct:'69%', chips:[
        {t:'Cypress avançado',c:'tool'},{t:'CI/CD',c:'hard'},{t:'Python/Java',c:'lang'},{t:'JMeter',c:'tool'},{t:'Trabalho em equipe',c:'soft'}
      ], diferencial:'Suite de testes integrada ao pipeline'},
      {n:'Liderança 5%', pct:'5%', chips:[
        {t:'Quality Engineering',c:'hard'},{t:'Observabilidade',c:'hard'},{t:'Liderança',c:'soft'}
      ], diferencial:'Redução mensurável de bugs em produção'}
    ],
    fonte:'Inteli — Índice de Vagas (Web Scraping, 2025)'
  },
  {
    id:'seg', nome:'Segurança da Informação', pct:2.5,
    descShort:'Proteção de dados, sistemas e infraestrutura. Menor volume público de vagas — muitas preenchidas por headhunting.',
    junior:17, pleno:76, lideranca:6,
    tipo:'esp',
    softSkills:[
      {t:'Criatividade',v:'33,4%'},{t:'Comunicação',v:'31,7%'},
      {t:'Organização',v:'23,9%'},{t:'Trabalho em equipe',v:'20,7%'}
    ],
    niveis:[
      {n:'Júnior 17%', pct:'17%', chips:[
        {t:'Linux',c:'hard'},{t:'Redes',c:'hard'},{t:'OWASP',c:'hard'},{t:'SIEM básico',c:'hard'},{t:'Criatividade',c:'soft'}
      ], diferencial:'CTFs (TryHackMe, HackTheBox) no currículo'},
      {n:'Pleno/Sênior 76%', pct:'76%', chips:[
        {t:'Splunk',c:'hard'},{t:'Linux',c:'hard'},{t:'AWS',c:'hard'},{t:'Pentest',c:'hard'},{t:'CEH/OSCP',c:'hard'}
      ], diferencial:'Resposta a incidentes reais + certificação CEH/OSCP'},
      {n:'Liderança 6%', pct:'6%', chips:[
        {t:'Zero-trust',c:'hard'},{t:'CISO-track',c:'hard'},{t:'Cloud Security',c:'hard'},{t:'Liderança',c:'soft'}
      ], diferencial:'Programa de segurança corporativa construído do zero'}
    ],
    fonte:'Inteli — Índice de Vagas (Web Scraping, 2025). Nota: parte das vagas é preenchida via headhunting, o que reduz o volume em plataformas públicas'
  },
  {
    id:'auto', nome:'Automação de Processos e Sistemas', pct:2.3,
    descShort:'Otimização de fluxos organizacionais via integração de sistemas e automação de tarefas repetitivas.',
    junior:40, pleno:50, lideranca:6,
    tipo:'entrada',
    softSkills:[
      {t:'Comunicação',v:'37,7%'},{t:'Organização',v:'22,1%'},
      {t:'Criatividade',v:'18,8%'},{t:'Trabalho em equipe',v:'13,6%'}
    ],
    niveis:[
      {n:'Júnior 40%', pct:'40%', chips:[
        {t:'Python',c:'lang'},{t:'Selenium',c:'tool'},{t:'Git',c:'tool'},{t:'API',c:'hard'},{t:'Organização',c:'soft'}
      ], diferencial:'Script real no portfólio'},
      {n:'Pleno/Sênior 50%', pct:'50%', chips:[
        {t:'Python avançado',c:'lang'},{t:'SAP',c:'hard'},{t:'CI/CD',c:'hard'},{t:'API',c:'hard'},{t:'Criatividade',c:'soft'}
      ], diferencial:'Automação end-to-end entregue'},
      {n:'Liderança 6%', pct:'6%', chips:[
        {t:'RPA',c:'hard'},{t:'IaC',c:'hard'},{t:'Cloud',c:'hard'},{t:'Liderança',c:'soft'}
      ], diferencial:'ROI mensurável das automações implementadas'}
    ],
    fonte:'Inteli — Índice de Vagas (Web Scraping, 2025)'
  }
];

var SALARIOS={
  dev:{
    min:6.8,max:26,
    axis:['8k','11k','14k','17k','20k','23k','26k'],
    roles:[
      {role:'Arquiteto de Software',jr:15.4,pl:20.1,sr:25.9},
      {role:'Desenvolvedor Mobile',jr:6.8,pl:11.7,sr:16.9},
      {role:'Desenvolvedor Full-Stack',jr:6.8,pl:12.4,sr:16.2},
      {role:'Desenvolvedor Back-End',jr:6.8,pl:12.3,sr:16.2},
      {role:'Desenvolvedor Front-End',jr:6.8,pl:12.3,sr:14.7}
    ]
  },
  infra:{
    min:4.4,max:28,
    axis:['5k','10k','15k','20k','25k','30k'],
    roles:[
      {role:'Gerente de Infraestrutura',jr:16.7,pl:21.7,sr:27.9},
      {role:'Analista de DevOps',jr:14.2,pl:18.5,sr:23.8},
      {role:'Coordenador de Infraestrutura',jr:11.6,pl:14.9,sr:19.1},
      {role:'Especialista de Cloud',jr:11.8,pl:14.8,sr:19.1},
      {role:'Analista de Infraestrutura',jr:5.6,pl:8.2,sr:12.2},
      {role:'Analista de Suporte',jr:4.4,pl:6.5,sr:8.4}
    ]
  },
  dados:{
    min:7,max:40,
    axis:['8k','15k','20k','25k','30k','35k','40k'],
    roles:[
      {role:'Gerente de Dados',jr:22.7,pl:29.4,sr:37.9},
      {role:'Gerente de BI',jr:19.4,pl:25.2,sr:32.5},
      {role:'Engenheiro de Inteligência Artificial',jr:19.5,pl:25,sr:27.1},
      {role:'Engenheiro de Prompt',jr:19,pl:22,sr:26.1},
      {role:'Especialista em IA e Machine Learning',jr:17.9,pl:20.2,sr:23.5},
      {role:'Especialista/Cientista de Dados',jr:14.7,pl:19.1,sr:24.6},
      {role:'Especialista de BI',jr:12.7,pl:16.5,sr:21.2},
      {role:'Analista de BI',jr:7,pl:10,sr:14.2}
    ]
  },
  projetos:{
    min:7.8,max:55,
    axis:['10k','20k','30k','40k','50k'],
    roles:[
      {role:'CIO — Chief Information Officer',jr:32,pl:41.5,sr:53.6},
      {role:'CTO — Chief Technology Officer',jr:29.6,pl:38.3,sr:49.5},
      {role:'Gerente de TI Generalista',jr:20.9,pl:27.2,sr:35},
      {role:'Gerente de Projetos',jr:13.8,pl:18.1,sr:23.3},
      {role:'Gerente de Produto',jr:11.4,pl:14.6,sr:18.6},
      {role:'Scrum Master',jr:10.9,pl:13.8,sr:17.6},
      {role:'Product Owner — PO',jr:7.8,pl:11.2,sr:14}
    ]
  },
  testes:{
    min:7.5,max:14,
    axis:['7k','8k','10k','12k','14k'],
    roles:[
      {role:'Analista de Testes',jr:7.5,pl:10.1,sr:13.1}
    ]
  },
  seg:{
    min:15.5,max:52.5,
    axis:['15k','25k','35k','45k','50k'],
    roles:[
      {role:'CSO — Chief Security Officer',jr:31.3,pl:40.6,sr:52.5},
      {role:'Gerente de Segurança da Informação',jr:22.2,pl:28.9,sr:37.2},
      {role:'Analista de DevSecOps',jr:15.5,pl:20.2,sr:26.2}
    ]
  },
  auto:{
    min:7.2,max:24.5,
    axis:['8k','12k','16k','20k','24k'],
    roles:[
      {role:'Consultor ERP',jr:14.7,pl:19.1,sr:24.5},
      {role:'Desenvolvedor RPA',jr:7.2,pl:12.2,sr:16.1},
      {role:'Analista de Sistemas',jr:7.2,pl:10.9,sr:14.4}
    ]
  }
};

function collectHardSkills(area){
  var seen={},list=[];
  area.niveis.forEach(function(n){
    n.chips.filter(function(c){return c.c!=='soft'}).forEach(function(c){
      if(!seen[c.t]){seen[c.t]=1;list.push(c)}
    });
  });
  return list;
}

function salaryPos(val,min,max){
  if(max<=min)return 50;
  return Math.max(4,Math.min(96,((val-min)/(max-min))*100));
}

function renderSalaryChart(areaId){
  var s=SALARIOS[areaId];
  if(!s)return '';
  var axisMin=parseFloat(s.axis[0]);
  var axisMax=parseFloat(s.axis[s.axis.length-1]);
  var rows=s.roles.map(function(r){
    var pj=salaryPos(r.jr,axisMin,axisMax);
    var pp=salaryPos(r.pl,axisMin,axisMax);
    var ps=salaryPos(r.sr,axisMin,axisMax);
    return '<div class="salary-row">'+
      '<div class="salary-role">'+r.role+'</div>'+
      '<div class="salary-track">'+
        '<span class="salary-dot jr" style="left:'+pj+'%"><span class="salary-dot-lbl">'+r.jr+'k</span></span>'+
        '<span class="salary-dot pl" style="left:'+pp+'%"><span class="salary-dot-lbl">'+r.pl+'k</span></span>'+
        '<span class="salary-dot sr" style="left:'+ps+'%"><span class="salary-dot-lbl">'+r.sr+'k</span></span>'+
      '</div></div>';
  }).join('');
  var axis=s.axis.map(function(a){return '<span>'+a+'</span>'}).join('');
  return '<div class="salary-chart">'+
    '<div class="salary-chart-h">Principais faixas salariais</div>'+
    '<div class="salary-chart-sub">Média salarial mensal (R$) por cargo — Júnior, Pleno e Sênior</div>'+
    '<div class="salary-leg">'+
      '<span><i class="leg-jr"></i>Júnior</span>'+
      '<span><i class="leg-pl"></i>Pleno</span>'+
      '<span><i class="leg-sr"></i>Sênior</span>'+
    '</div>'+
    '<div class="salary-grid">'+rows+
    '<div class="salary-axis">'+axis+'</div></div>'+
  '</div>';
}

/* ══ RENDER AREA CARDS ══ */
var grid=document.getElementById('areasGrid');if(!grid)return;
let activeCard = null;
let activeDetail = null;

function getSeniorityColors(area) {
  return `
    <div class="seniority-bar">
      <div class="s-jr" style="flex:${area.junior}"></div>
      <div class="s-pl" style="flex:${area.pleno}"></div>
      <div class="s-lid" style="flex:${area.lideranca}"></div>
    </div>
    <div class="seniority-legend">
      <span><span class="dot" style="background:var(--teal)"></span>Jr ${area.junior}%</span>
      <span><span class="dot" style="background:#5b5480"></span>Pleno ${area.pleno}%</span>
      <span><span class="dot" style="background:var(--coral)"></span>Lid ${area.lideranca}%</span>
    </div>`;
}

function renderDetail(area) {
  const ss = area.softSkills.map(s=>
    `<span class="chip soft">${s.t} <strong style="margin-left:.2rem;font-size:.62rem">${s.v}</strong></span>`
  ).join('');
  const hard = collectHardSkills(area).map(c=>
    `<span class="chip ${c.c}">${c.t}</span>`
  ).join('');

  return `<div class="area-detail" id="detail-${area.id}">
    <div>
      <div class="detail-col-title">Soft skills mais demandadas</div>
      <div class="chip-group">${ss}</div>
    </div>
    <div>
      <div class="detail-col-title">Hard skills mais demandadas</div>
      <div class="chip-group">${hard}</div>
    </div>
    <div class="detail-salary">${renderSalaryChart(area.id)}</div>
    <div class="detail-source">Competências: ${area.fonte} · Salários: Guia Salarial (Robert Half, 2026)</div>
  </div>`;
}

function renderCards(filter) {
  grid.innerHTML = '';
  const filtered = filter==="all"?AREAS_DATA
    : filter === 'entrada' ? AREAS_DATA.filter(a=>a.junior > 30)
    : AREAS_DATA.filter(a=>a.tipo==='esp');

  filtered.forEach(area => {
    const card = document.createElement('div');
    card.className='area-card';
    card.dataset.id = area.id;

    let badgeHtml = '';
    if(area.tipo==='entrada') badgeHtml = `<span class="area-badge badge-entrada">Porta de entrada</span>`;
    else if(area.tipo==='esp') badgeHtml = `<span class="area-badge badge-esp">Alta especializ.</span>`;

    card.innerHTML = `
      <div class="area-header">
        <div class="area-pct">${area.pct}%</div>
        ${badgeHtml}
      </div>
      <div class="area-name">${area.nome}</div>
      <div class="area-desc-short">${area.descShort}</div>
      ${getSeniorityColors(area)}
      <div class="area-toggle">+</div>`;

    card.addEventListener('click', () => toggleDetail(area, card));
    grid.appendChild(card);
  });

}

function toggleDetail(area, card) {
  const isOpen = card.classList.contains('open');
  // close any open
  if(activeCard && activeCard !== card) {
    activeCard.classList.remove('open');
    activeCard.querySelector('.area-toggle').textContent = '+';
  }
  if(activeDetail) {
    activeDetail.classList.remove('show');
    activeDetail.remove();
  }

  if(isOpen) {
    card.classList.remove('open');
    card.querySelector('.area-toggle').textContent = '+';
    activeCard = null; activeDetail = null;
    return;
  }

  card.classList.add('open');
  card.querySelector('.area-toggle').textContent = '×';
  activeCard = card;

  const detailEl = document.createElement('div');
  detailEl.innerHTML = renderDetail(area);
  const panel = detailEl.firstElementChild;
  panel.classList.add('show');

  // insert after card's row
  card.after(panel);
  activeDetail = panel;

  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

document.querySelectorAll('#visao-area .filter-btn').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('#visao-area .filter-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    if(activeDetail) { activeDetail.classList.remove('show'); activeDetail.remove(); activeDetail = null; }
    if(activeCard) { activeCard.classList.remove('open'); activeCard = null; }
    renderCards(btn.dataset.filter);
  });
});

  renderCards('all');
})();
