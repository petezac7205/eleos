// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title EleosRegistryV2
 * @dev Immutable on-chain audit and proof log for the Eleos Transparent Charity Platform.
 * Features:
 * 1. Multi-Role RBAC (Decentralized AccessControl replacing single onlyOwner)
 *    - DEFAULT_ADMIN_ROLE: Controlled by Community Multi-Sig / DAO Timelock
 *    - AUDITOR_ROLE: Granted to independent certified auditor firms for co-signing milestone proofs
 *    - RELAYER_ROLE: Granted to automated gateway oracles for fiat/UPI payment broadcasts
 *    - Permissionless Public: Whistleblower flags and Merkle proof verification open to anyone
 * 2. Daily Merkle Root State Commitments (anchorDailyState) to prove DB integrity
 * 3. On-chain & Off-chain O(log N) Merkle Proof verification (verifyDatabaseRecord)
 */
contract EleosRegistryV2 {

    // =========================================================================
    // ROLES & ACCESS CONTROL
    // =========================================================================

    bytes32 public constant DEFAULT_ADMIN_ROLE = 0x00;
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR_ROLE");
    bytes32 public constant RELAYER_ROLE = keccak256("RELAYER_ROLE");

    mapping(bytes32 => mapping(address => bool)) private _roles;
    mapping(bytes32 => bytes32) private _roleAdmin;

    event RoleGranted(bytes32 indexed role, address indexed account, address indexed sender);
    event RoleRevoked(bytes32 indexed role, address indexed account, address indexed sender);
    event RoleAdminChanged(bytes32 indexed role, bytes32 indexed previousAdminRole, bytes32 indexed newAdminRole);

    modifier onlyRole(bytes32 role) {
        require(hasRole(role, msg.sender), "EleosRegistry: caller lacks required role");
        _;
    }

    // =========================================================================
    // EVENTS (Public Audit Trail on Polygon)
    // =========================================================================

    event DonationRecorded(
        bytes32 indexed donationId,
        bytes32 indexed campaignId,
        bytes32 gatewayReceiptHash,
        uint256 amountPaise,
        string currency,
        uint256 timestamp
    );

    event MilestoneUpdated(
        bytes32 indexed campaignId,
        uint8 milestoneIndex,
        bytes32 evidenceHash,
        address indexed attestationSigner,
        string status,
        uint256 timestamp
    );

    event DonationRefunded(
        bytes32 indexed donationId,
        bytes32 indexed campaignId,
        uint256 amountPaise,
        string reason,
        uint256 timestamp
    );

    event ScoreSnapshot(
        bytes32 indexed ngoId,
        bytes32 scoreHash,
        uint8 overallScore,
        string label,
        uint256 timestamp
    );

    event VolunteerCredential(
        bytes32 indexed credentialId,
        bytes32 indexed campaignId,
        bytes32 volunteerHash,
        uint16 hoursCount,
        uint256 timestamp
    );

    event CampaignCreated(
        bytes32 indexed campaignId,
        bytes32 indexed ngoId,
        uint256 targetAmountPaise,
        string currency,
        uint256 timestamp
    );

    event DocumentAnchored(
        bytes32 indexed ngoId,
        string docType,
        bytes32 fileHash,
        uint256 timestamp
    );

    event ExpenseRecorded(
        bytes32 indexed campaignId,
        uint8 milestoneIndex,
        uint256 amountPaise,
        bytes32 vendorGstHash,
        bytes32 invoiceHash,
        uint256 timestamp
    );

    event CampaignBudgetLocked(
        bytes32 indexed campaignId,
        bytes32 budgetItemsHash,
        uint256 targetAmountPaise,
        uint256 timestamp
    );

    event CampaignFlagged(
        bytes32 indexed campaignId,
        string reasonCode,
        bytes32 evidenceHash,
        address indexed reporter,
        uint256 timestamp
    );

    event DailyStateAnchored(
        bytes32 indexed merkleRoot,
        uint256 indexed dateTimestamp,
        uint32 recordCount,
        uint256 timestamp
    );

    // =========================================================================
    // CONSTRUCTOR & ROLE MANAGEMENT
    // =========================================================================

    constructor(address initialAdmin) {
        address admin = initialAdmin == address(0) ? msg.sender : initialAdmin;
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(RELAYER_ROLE, admin);
        _grantRole(AUDITOR_ROLE, admin);
    }

    function hasRole(bytes32 role, address account) public view returns (bool) {
        return _roles[role][account];
    }

    function getRoleAdmin(bytes32 role) public view returns (bytes32) {
        return _roleAdmin[role];
    }

    function grantRole(bytes32 role, address account) public onlyRole(getRoleAdmin(role)) {
        _grantRole(role, account);
    }

    function revokeRole(bytes32 role, address account) public onlyRole(getRoleAdmin(role)) {
        _revokeRole(role, account);
    }

    function renounceRole(bytes32 role) public {
        _revokeRole(role, msg.sender);
    }

    function _grantRole(bytes32 role, address account) internal {
        if (!hasRole(role, account)) {
            _roles[role][account] = true;
            emit RoleGranted(role, account, msg.sender);
        }
    }

    function _revokeRole(bytes32 role, address account) internal {
        if (hasRole(role, account)) {
            _roles[role][account] = false;
            emit RoleRevoked(role, account, msg.sender);
        }
    }

    // =========================================================================
    // REGISTRATION FUNCTIONS (Role-Protected & Public)
    // =========================================================================

    /**
     * @dev Broadcasts fiat/UPI donation confirmation on-chain.
     * Accessible by RELAYER_ROLE (e.g. gateway webhook relays).
     */
    function recordDonation(
        bytes32 donationId,
        bytes32 campaignId,
        bytes32 gatewayReceiptHash,
        uint256 amountPaise,
        string calldata currency
    ) external onlyRole(RELAYER_ROLE) {
        emit DonationRecorded(
            donationId,
            campaignId,
            gatewayReceiptHash,
            amountPaise,
            currency,
            block.timestamp
        );
    }

    /**
     * @dev Records refund event on-chain.
     */
    function recordRefund(
        bytes32 donationId,
        bytes32 campaignId,
        uint256 amountPaise,
        string calldata reason
    ) external onlyRole(RELAYER_ROLE) {
        emit DonationRefunded(
            donationId,
            campaignId,
            amountPaise,
            reason,
            block.timestamp
        );
    }

    /**
     * @dev Records milestone progress & evidence submission.
     * Accessible by AUDITOR_ROLE (independent certified auditors & field inspectors).
     */
    function updateMilestone(
        bytes32 campaignId,
        uint8 milestoneIndex,
        bytes32 evidenceHash,
        address attestationSigner,
        string calldata status
    ) external onlyRole(AUDITOR_ROLE) {
        address signer = attestationSigner == address(0) ? msg.sender : attestationSigner;
        emit MilestoneUpdated(
            campaignId,
            milestoneIndex,
            evidenceHash,
            signer,
            status,
            block.timestamp
        );
    }

    /**
     * @dev Records explainable AI Trustability & Feasibility score snapshot.
     */
    function snapshotScore(
        bytes32 ngoId,
        bytes32 scoreHash,
        uint8 overallScore,
        string calldata label
    ) external onlyRole(RELAYER_ROLE) {
        emit ScoreSnapshot(
            ngoId,
            scoreHash,
            overallScore,
            label,
            block.timestamp
        );
    }

    /**
     * @dev Issues immutable volunteer service credential proof.
     */
    function issueVolunteerCredential(
        bytes32 credentialId,
        bytes32 campaignId,
        bytes32 volunteerHash,
        uint16 hoursCount
    ) external onlyRole(AUDITOR_ROLE) {
        emit VolunteerCredential(
            credentialId,
            campaignId,
            volunteerHash,
            hoursCount,
            block.timestamp
        );
    }

    /**
     * @dev Records newly approved campaign and target budget on-chain.
     */
    function createCampaign(
        bytes32 campaignId,
        bytes32 ngoId,
        uint256 targetAmountPaise,
        string calldata currency
    ) external onlyRole(RELAYER_ROLE) {
        emit CampaignCreated(
            campaignId,
            ngoId,
            targetAmountPaise,
            currency,
            block.timestamp
        );
    }

    /**
     * @dev Anchors NGO legal compliance document (12A, 80G, FCRA, audit report).
     */
    function anchorDocument(
        bytes32 ngoId,
        string calldata docType,
        bytes32 fileHash
    ) external onlyRole(RELAYER_ROLE) {
        emit DocumentAnchored(
            ngoId,
            docType,
            fileHash,
            block.timestamp
        );
    }

    /**
     * @dev Records commercial vendor invoice and outflow against milestone.
     */
    function recordExpense(
        bytes32 campaignId,
        uint8 milestoneIndex,
        uint256 amountPaise,
        bytes32 vendorGstHash,
        bytes32 invoiceHash
    ) external onlyRole(AUDITOR_ROLE) {
        emit ExpenseRecorded(
            campaignId,
            milestoneIndex,
            amountPaise,
            vendorGstHash,
            invoiceHash,
            block.timestamp
        );
    }

    /**
     * @dev Freezes itemized unit-cost budget breakdown on-chain.
     */
    function lockCampaignBudget(
        bytes32 campaignId,
        bytes32 budgetItemsHash,
        uint256 targetAmountPaise
    ) external onlyRole(RELAYER_ROLE) {
        emit CampaignBudgetLocked(
            campaignId,
            budgetItemsHash,
            targetAmountPaise,
            block.timestamp
        );
    }

    /**
     * @dev Permissionless whistleblower reporting: ANY Web3 address can flag a campaign.
     */
    function flagCampaign(
        bytes32 campaignId,
        string calldata reasonCode,
        bytes32 evidenceHash
    ) external {
        emit CampaignFlagged(
            campaignId,
            reasonCode,
            evidenceHash,
            msg.sender,
            block.timestamp
        );
    }

    // =========================================================================
    // DAILY MERKLE ROOT COMMITMENTS & PROOF VERIFICATION
    // =========================================================================

    /**
     * @dev Anchors the daily Merkle Root of the entire platform database state.
     * Prevents any silent database tampering, record deletion, or fabrication.
     */
    function anchorDailyState(
        bytes32 merkleRoot,
        uint256 dateTimestamp,
        uint32 recordCount
    ) external onlyRole(RELAYER_ROLE) {
        emit DailyStateAnchored(
            merkleRoot,
            dateTimestamp,
            recordCount,
            block.timestamp
        );
    }

    /**
     * @dev Pure cryptographic Merkle Proof verification function (O(log N)).
     * Can be invoked on-chain or off-chain via Web3 eth_call with zero gas.
     */
    function verifyDatabaseRecord(
        bytes32 leafHash,
        bytes32[] calldata merkleProof,
        bytes32 expectedRoot
    ) external pure returns (bool) {
        bytes32 computedHash = leafHash;
        for (uint256 i = 0; i < merkleProof.length; i++) {
            bytes32 proofElement = merkleProof[i];
            if (computedHash <= proofElement) {
                computedHash = keccak256(abi.encodePacked(computedHash, proofElement));
            } else {
                computedHash = keccak256(abi.encodePacked(proofElement, computedHash));
            }
        }
        return computedHash == expectedRoot;
    }
}

