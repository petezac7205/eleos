// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title EleosRegistry
 * @dev Immutable on-chain audit and proof log for the Eleos Transparent Charity Platform.
 * Uses lightweight indexed event logs to provide publicly auditable proofs on Polygon PoS
 * with minimum gas footprint (~5x cheaper than storage writes).
 */
contract EleosRegistry {
    address public owner;
    address public pendingOwner;

    // =========================================================================
    // EVENTS (Public Audit Trail on Polygon)
    // =========================================================================

    /**
     * @dev Emitted when ownership transfer is initiated.
     */
    event OwnershipTransferStarted(address indexed previousOwner, address indexed newOwner);

    /**
     * @dev Emitted when ownership transfer is finalized.
     */
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /**
     * @dev Emitted when a fiat/UPI donation is confirmed on Eleos.
     * Includes gatewayReceiptHash (e.g., keccak256 hash of gateway signature + payment id)
     * so third parties can verify transaction authenticity without trusting Eleos's database.
     */
    event DonationRecorded(
        bytes32 indexed donationId,
        bytes32 indexed campaignId,
        bytes32 gatewayReceiptHash,
        uint256 amountPaise,
        string currency,
        uint256 timestamp
    );

    /**
     * @dev Emitted when an NGO submits verified evidence for a project milestone.
     * Includes attestationSigner (e.g. NGO key or verified auditor address) for co-signing.
     */
    event MilestoneUpdated(
        bytes32 indexed campaignId,
        uint8 milestoneIndex,
        bytes32 evidenceHash,
        address indexed attestationSigner,
        string status,          // e.g., "verified", "submitted"
        uint256 timestamp
    );

    /**
     * @dev Emitted when a donation is marked refunded on-chain.
     */
    event DonationRefunded(
        bytes32 indexed donationId,
        bytes32 indexed campaignId,
        uint256 amountPaise,
        string reason,
        uint256 timestamp
    );

    /**
     * @dev Emitted when AI Trustability or Feasibility scoring snapshot is generated.
     */
    event ScoreSnapshot(
        bytes32 indexed ngoId,
        bytes32 scoreHash,      // SHA-256 hash of complete explainable score JSON
        uint8 overallScore,
        string label,           // e.g., "verified", "high_risk", "moderate"
        uint256 timestamp
    );

    /**
     * @dev Emitted when volunteer hours are completed and signed off by the NGO.
     */
    event VolunteerCredential(
        bytes32 indexed credentialId,
        bytes32 indexed campaignId,
        bytes32 volunteerHash,  // SHA-256 hash of volunteer identity
        uint16 hoursCount,
        uint256 timestamp
    );

    /**
     * @dev Emitted when a new campaign is reviewed and approved on Eleos.
     */
    event CampaignCreated(
        bytes32 indexed campaignId,
        bytes32 indexed ngoId,
        uint256 targetAmountPaise,
        string currency,
        uint256 timestamp
    );

    /**
     * @dev Emitted when an NGO compliance document (12A, 80G, FCRA, audit report) is anchored.
     */
    event DocumentAnchored(
        bytes32 indexed ngoId,
        string docType,         // e.g., "12a_cert", "80g_cert", "audit_report", "pan_card"
        bytes32 fileHash,       // SHA-256 checksum of original PDF/file
        uint256 timestamp
    );

    /**
     * @dev Emitted when an expense payment / vendor invoice is recorded against a milestone.
     */
    event ExpenseRecorded(
        bytes32 indexed campaignId,
        uint8 milestoneIndex,
        uint256 amountPaise,
        bytes32 vendorGstHash,  // SHA-256 hash of Vendor GSTIN / identifier
        bytes32 invoiceHash,    // SHA-256 checksum of commercial invoice PDF
        uint256 timestamp
    );

    /**
     * @dev Emitted when an itemized campaign budget breakdown is locked on-chain.
     */
    event CampaignBudgetLocked(
        bytes32 indexed campaignId,
        bytes32 budgetItemsHash,// SHA-256 hash of itemized unit costs JSON
        uint256 targetAmountPaise,
        uint256 timestamp
    );

    /**
     * @dev Emitted when a dispute, red-flag, or whistleblower report is logged on-chain.
     */
    event CampaignFlagged(
        bytes32 indexed campaignId,
        string reasonCode,      // e.g., "misleading_evidence", "vendor_mismatch", "budget_dispute"
        bytes32 evidenceHash,   // SHA-256 hash of dispute report / proof
        uint256 timestamp
    );

    // =========================================================================
    // MODIFIERS & CONSTRUCTOR
    // =========================================================================

    modifier onlyOwner() {
        require(msg.sender == owner, "EleosRegistry: caller is not authorized owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    // =========================================================================
    // REGISTRATION FUNCTIONS (Owner-Only Broadcaster)
    // =========================================================================

    function recordDonation(
        bytes32 donationId,
        bytes32 campaignId,
        bytes32 gatewayReceiptHash,
        uint256 amountPaise,
        string calldata currency
    ) external onlyOwner {
        emit DonationRecorded(
            donationId,
            campaignId,
            gatewayReceiptHash,
            amountPaise,
            currency,
            block.timestamp
        );
    }

    function recordRefund(
        bytes32 donationId,
        bytes32 campaignId,
        uint256 amountPaise,
        string calldata reason
    ) external onlyOwner {
        emit DonationRefunded(
            donationId,
            campaignId,
            amountPaise,
            reason,
            block.timestamp
        );
    }

    function updateMilestone(
        bytes32 campaignId,
        uint8 milestoneIndex,
        bytes32 evidenceHash,
        address attestationSigner,
        string calldata status
    ) external onlyOwner {
        emit MilestoneUpdated(
            campaignId,
            milestoneIndex,
            evidenceHash,
            attestationSigner,
            status,
            block.timestamp
        );
    }

    function snapshotScore(
        bytes32 ngoId,
        bytes32 scoreHash,
        uint8 overallScore,
        string calldata label
    ) external onlyOwner {
        emit ScoreSnapshot(
            ngoId,
            scoreHash,
            overallScore,
            label,
            block.timestamp
        );
    }

    function issueVolunteerCredential(
        bytes32 credentialId,
        bytes32 campaignId,
        bytes32 volunteerHash,
        uint16 hoursCount
    ) external onlyOwner {
        emit VolunteerCredential(
            credentialId,
            campaignId,
            volunteerHash,
            hoursCount,
            block.timestamp
        );
    }

    function createCampaign(
        bytes32 campaignId,
        bytes32 ngoId,
        uint256 targetAmountPaise,
        string calldata currency
    ) external onlyOwner {
        emit CampaignCreated(
            campaignId,
            ngoId,
            targetAmountPaise,
            currency,
            block.timestamp
        );
    }

    function anchorDocument(
        bytes32 ngoId,
        string calldata docType,
        bytes32 fileHash
    ) external onlyOwner {
        emit DocumentAnchored(
            ngoId,
            docType,
            fileHash,
            block.timestamp
        );
    }

    function recordExpense(
        bytes32 campaignId,
        uint8 milestoneIndex,
        uint256 amountPaise,
        bytes32 vendorGstHash,
        bytes32 invoiceHash
    ) external onlyOwner {
        emit ExpenseRecorded(
            campaignId,
            milestoneIndex,
            amountPaise,
            vendorGstHash,
            invoiceHash,
            block.timestamp
        );
    }

    function lockCampaignBudget(
        bytes32 campaignId,
        bytes32 budgetItemsHash,
        uint256 targetAmountPaise
    ) external onlyOwner {
        emit CampaignBudgetLocked(
            campaignId,
            budgetItemsHash,
            targetAmountPaise,
            block.timestamp
        );
    }

    function flagCampaign(
        bytes32 campaignId,
        string calldata reasonCode,
        bytes32 evidenceHash
    ) external onlyOwner {
        emit CampaignFlagged(
            campaignId,
            reasonCode,
            evidenceHash,
            block.timestamp
        );
    }

    /**
     * @dev Step 1 of 2-step ownership transfer. Initiates transfer to newOwner.
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "EleosRegistry: zero address not allowed");
        require(newOwner != owner, "EleosRegistry: already owner");
        pendingOwner = newOwner;
        emit OwnershipTransferStarted(owner, newOwner);
    }

    /**
     * @dev Step 2 of 2-step ownership transfer. Pending owner accepts ownership.
     */
    function acceptOwnership() external {
        require(msg.sender == pendingOwner, "EleosRegistry: caller is not pending owner");
        address oldOwner = owner;
        owner = pendingOwner;
        pendingOwner = address(0);
        emit OwnershipTransferred(oldOwner, owner);
    }
}

