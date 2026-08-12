class AdvisorBookServiceError(RuntimeError):
    def __init__(self, *, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def source_unavailable() -> AdvisorBookServiceError:
    return AdvisorBookServiceError(
        code="advisor_book_source_unavailable",
        message="Advisor-book information is temporarily unavailable.",
        status_code=502,
    )


def source_contract_invalid() -> AdvisorBookServiceError:
    return AdvisorBookServiceError(
        code="advisor_book_source_contract_invalid",
        message="Advisor-book information could not be safely verified.",
        status_code=502,
    )


def source_incomplete() -> AdvisorBookServiceError:
    return AdvisorBookServiceError(
        code="advisor_book_source_incomplete",
        message="Advisor-book membership is incomplete and cannot verify portfolio selection.",
        status_code=502,
    )


def tenant_scope_unverified() -> AdvisorBookServiceError:
    return AdvisorBookServiceError(
        code="advisor_book_tenant_scope_unverified",
        message="Advisor-book tenant scope could not be safely verified.",
        status_code=502,
    )


def portfolio_selection_unavailable() -> AdvisorBookServiceError:
    return AdvisorBookServiceError(
        code="advisor_book_portfolio_not_available",
        message="One or more selected portfolios are not available in the authenticated book.",
        status_code=403,
    )


def portfolio_selection_inactive() -> AdvisorBookServiceError:
    return AdvisorBookServiceError(
        code="advisor_book_portfolio_inactive",
        message="One or more selected portfolios are not active for reporting.",
        status_code=409,
    )
