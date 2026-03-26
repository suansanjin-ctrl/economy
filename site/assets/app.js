(function () {
  const manifest = window.REPORTS_MANIFEST || { generatedAt: null, reports: [] };
  const reports = Array.isArray(manifest.reports) ? manifest.reports : [];

  const reportCount = document.getElementById("report-count");
  const generatedAt = document.getElementById("generated-at");
  const reportSelect = document.getElementById("report-select");
  const reportList = document.getElementById("report-list");
  const currentTitle = document.getElementById("current-title");
  const currentMeta = document.getElementById("current-meta");
  const openReport = document.getElementById("open-report");
  const shareReport = document.getElementById("share-report");
  const emptyState = document.getElementById("empty-state");
  const reportFrame = document.getElementById("report-frame");

  const reportById = new Map(reports.map((report) => [report.id, report]));

  function formatDate(value) {
    if (!value) {
      return "未设置";
    }

    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }

    return parsed.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function buildShareHref(reportId) {
    const url = new URL(window.location.href);
    url.searchParams.set("report", reportId);
    return url.toString();
  }

  function renderOptions() {
    reportSelect.innerHTML = "";

    if (!reports.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "暂无内容";
      reportSelect.appendChild(option);
      return;
    }

    reports.forEach((report) => {
      const option = document.createElement("option");
      option.value = report.id;
      option.textContent = `${report.title} (${report.date})`;
      reportSelect.appendChild(option);
    });
  }

  function renderCards(activeId) {
    reportList.innerHTML = "";

    reports.forEach((report) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "report-card";
      if (report.id === activeId) {
        button.classList.add("active");
      }

      const title = document.createElement("p");
      title.className = "report-title";
      title.textContent = report.title;

      const date = document.createElement("p");
      date.className = "report-date";
      date.textContent = `日期：${report.date}`;

      const file = document.createElement("p");
      file.className = "report-file";
      file.textContent = `文件：${report.originalName}`;

      button.append(title, date, file);
      button.addEventListener("click", function () {
        selectReport(report.id);
      });
      reportList.appendChild(button);
    });
  }

  function selectReport(reportId) {
    const report = reportById.get(reportId);
    if (!report) {
      return;
    }

    currentTitle.textContent = report.title;
    currentMeta.textContent = `日期：${report.date} · 添加时间：${formatDate(report.addedAt)}`;
    openReport.href = report.href;
    shareReport.dataset.href = buildShareHref(report.id);
    reportFrame.src = report.href;
    reportFrame.classList.add("visible");
    emptyState.hidden = true;
    reportSelect.value = report.id;
    renderCards(report.id);

    const url = new URL(window.location.href);
    url.searchParams.set("report", report.id);
    window.history.replaceState({}, "", url);
  }

  shareReport.addEventListener("click", async function (event) {
    event.preventDefault();
    const href = shareReport.dataset.href;
    if (!href) {
      return;
    }

    try {
      await navigator.clipboard.writeText(href);
      shareReport.textContent = "已复制链接";
      window.setTimeout(function () {
        shareReport.textContent = "复制当前链接";
      }, 1800);
    } catch (error) {
      window.open(href, "_blank", "noreferrer");
    }
  });

  reportSelect.addEventListener("change", function () {
    if (reportSelect.value) {
      selectReport(reportSelect.value);
    }
  });

  reportCount.textContent = String(reports.length);
  generatedAt.textContent = formatDate(manifest.generatedAt);
  renderOptions();

  if (!reports.length) {
    openReport.href = "#";
    shareReport.href = "#";
    return;
  }

  const params = new URLSearchParams(window.location.search);
  const initialReportId = params.get("report") && reportById.has(params.get("report"))
    ? params.get("report")
    : reports[0].id;

  selectReport(initialReportId);
})();

