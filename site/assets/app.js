(function () {
  const manifest = window.REPORTS_MANIFEST || { generatedAt: null, reports: [] };
  const reports = Array.isArray(manifest.reports) ? manifest.reports : [];

  const reportCount = document.getElementById("report-count");
  const generatedAt = document.getElementById("generated-at");
  const reportSelect = document.getElementById("report-select");
  const reportList = document.getElementById("report-list");
  const currentTitle = document.getElementById("current-title");
  const currentMeta = document.getElementById("current-meta");
  const openReportCurrent = document.getElementById("open-report-current");
  const openReport = document.getElementById("open-report");
  const shareReport = document.getElementById("share-report");
  const emptyState = document.getElementById("empty-state");
  const viewerHint = document.getElementById("viewer-hint");

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
      const link = document.createElement("a");
      link.className = "report-card";
      link.href = report.href;
      if (report.id === activeId) {
        link.classList.add("active");
      }

      const title = document.createElement("p");
      title.className = "report-title";
      title.textContent = report.title;

      const date = document.createElement("p");
      date.className = "report-date";
      date.textContent = `日期：${report.date}`;

      const file = document.createElement("p");
      file.className = "report-file";
      file.textContent = `文件：${report.originalName} · 点击直接打开`;

      link.append(title, date, file);
      reportList.appendChild(link);
    });
  }

  function selectReport(reportId) {
    const report = reportById.get(reportId);
    if (!report) {
      return;
    }

    currentTitle.textContent = report.title;
    currentMeta.textContent = `日期：${report.date} · 添加时间：${formatDate(report.addedAt)}`;
    openReportCurrent.href = report.href;
    openReport.href = report.href;
    shareReport.dataset.href = buildShareHref(report.id);
    emptyState.hidden = true;
    viewerHint.hidden = false;
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
    openReportCurrent.href = "#";
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
